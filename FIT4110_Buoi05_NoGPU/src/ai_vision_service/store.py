"""SQLite-backed persistence cho detection + face-match results.

Buổi 05 thay thế in-memory store bằng SQLite để dữ liệu sống sót qua container
restart. SQLite được chọn vì:
  - Zero-config, không cần image riêng cho DB.
  - Vẫn đảm bảo đa-service qua docker-compose (volume mount).
  - Phù hợp với lab NoGPU (không yêu cầu Postgres/TimescaleDB).

Khi nhóm muốn dùng Postgres thật, chỉ cần thay đường dẫn DB_PATH bằng
chuỗi kết nối psycopg2 và viết lại hàm _connect().
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schemas import DetectResponse, FaceMatchResponse

DB_PATH = Path(os.environ.get("VISION_DB_PATH", "/data/vision.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_LOCK = threading.Lock()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Tạo schema nếu chưa tồn tại. Idempotent."""
    with _LOCK, _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS detections (
                detection_id   TEXT PRIMARY KEY,
                camera_id      TEXT NOT NULL,
                payload_json   TEXT NOT NULL,
                created_at     TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS ix_detections_created_at
                ON detections(created_at DESC);
            CREATE INDEX IF NOT EXISTS ix_detections_camera
                ON detections(camera_id);

            CREATE TABLE IF NOT EXISTS face_matches (
                match_id       TEXT PRIMARY KEY,
                trace_id       TEXT,
                payload_json   TEXT NOT NULL,
                created_at     TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS ix_face_matches_created_at
                ON face_matches(created_at DESC);
            """
        )


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class VisionStore:
    """Lớp persistence thread-safe cho Vision Service."""

    def __init__(self) -> None:
        init_db()

    def add_detection(self, response: DetectResponse) -> None:
        with _LOCK, _connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO detections(detection_id, camera_id, payload_json, created_at) "
                "VALUES (?, ?, ?, ?)",
                (
                    response.detection_id,
                    response.camera_id,
                    response.model_dump_json(),
                    _now(),
                ),
            )

    def get_detection(self, detection_id: str) -> DetectResponse | None:
        with _LOCK, _connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM detections WHERE detection_id = ?",
                (detection_id,),
            ).fetchone()
        if not row:
            return None
        return DetectResponse.model_validate_json(row["payload_json"])

    def list_recent_detections(
        self,
        limit: int,
        camera_id: str | None = None,
    ) -> tuple[list[DetectResponse], str | None, bool]:
        params: list[Any] = []
        where = ""
        if camera_id:
            where = "WHERE camera_id = ?"
            params.append(camera_id)
        params.append(limit + 1)  # peek next
        sql = (
            f"SELECT payload_json FROM detections {where} "
            "ORDER BY created_at DESC LIMIT ?"
        )
        with _LOCK, _connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        items: list[DetectResponse] = []
        for row in rows[:limit]:
            items.append(DetectResponse.model_validate_json(row["payload_json"]))
        has_more = len(rows) > limit
        next_cursor = items[-1].timestamp if items and has_more else None
        return items, next_cursor, has_more

    def add_face_match(self, response: FaceMatchResponse) -> None:
        with _LOCK, _connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO face_matches(match_id, trace_id, payload_json, created_at) "
                "VALUES (?, ?, ?, ?)",
                (
                    response.match_id,
                    response.trace_id,
                    response.model_dump_json(),
                    _now(),
                ),
            )

    def stats(self) -> dict[str, int]:
        with _LOCK, _connect() as conn:
            detections = conn.execute("SELECT COUNT(*) AS c FROM detections").fetchone()["c"]
            face_matches = conn.execute("SELECT COUNT(*) AS c FROM face_matches").fetchone()["c"]
        return {"detections": detections, "face_matches": face_matches}

    def ping(self) -> bool:
        """Kiểm tra nhanh connection còn mở không — dùng cho /ready."""
        try:
            with _LOCK, _connect() as conn:
                conn.execute("SELECT 1").fetchone()
            return True
        except sqlite3.Error:
            return False