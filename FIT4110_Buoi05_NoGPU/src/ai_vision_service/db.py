"""MySQL connection pool cho AI Vision Service.

Tự động kết nối đến MySQL qua biến môi trường:
  MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

Migrate từ SQLite store (Buổi 04) sang MySQL (Buổi 05 NoGPU).
Pool size nhỏ vì service chỉ ghi detection khi có request.
"""
from __future__ import annotations

import json
import logging
import os
from contextlib import contextmanager
from typing import Any, Generator

import mysql.connector
from mysql.connector import pooling

LOGGER = logging.getLogger("ai_vision.db")

_POOL: pooling.MySQLConnectionPool | None = None


def _pool() -> pooling.MySQLConnectionPool:
    global _POOL
    if _POOL is None:
        _POOL = pooling.MySQLConnectionPool(
            pool_name="ai_vision_pool",
            pool_size=3,
            pool_reset_session=True,
            host=os.environ["MYSQL_HOST"],
            port=int(os.environ["MYSQL_PORT"]),
            user=os.environ["MYSQL_USER"],
            password=os.environ["MYSQL_PASSWORD"],
            database=os.environ["MYSQL_DATABASE"],
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
            autocommit=True,
        )
        LOGGER.info(
            "MySQL pool connected to %s:%s/%s",
            os.environ["MYSQL_HOST"],
            os.environ["MYSQL_PORT"],
            os.environ["MYSQL_DATABASE"],
        )
    return _POOL


@contextmanager
def get_connection() -> Generator[Any, None, None]:
    """Context manager: lấy connection từ pool, tự động trả về."""
    conn = _pool().get_connection()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_cursor(commit: bool = True) -> Generator[Any, None, None]:
    """Context manager: cursor với commit tự động."""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            yield cursor
            if commit:
                conn.commit()
        finally:
            cursor.close()


def ping() -> bool:
    """Kiểm tra kết nối MySQL còn sống không."""
    try:
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return True
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("MySQL ping failed: %s", exc)
        return False


def stats() -> dict[str, int]:
    """Đếm số bản ghi trong các bảng chính."""
    try:
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM detections")
            detections = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) as cnt FROM face_matches")
            face_matches = cur.fetchone()["cnt"]
        return {"detections": detections, "face_matches": face_matches}
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("MySQL stats failed: %s", exc)
        return {"detections": 0, "face_matches": 0}


# ─────────────────────────────────────────────────────────────────────────────
# Detection operations
# ─────────────────────────────────────────────────────────────────────────────

def insert_detection(
    detection_id: str,
    camera_id: str,
    detections_json: str,
    risk_level: str,
    model_version: str,
    processing_time_ms: int,
    timestamp: str,
) -> None:
    """Lưu một detection record vào MySQL."""
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO detections
                (detection_id, camera_id, detections, risk_level,
                 model_version, processing_time_ms, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                camera_id = VALUES(camera_id),
                detections = VALUES(detections),
                risk_level = VALUES(risk_level),
                model_version = VALUES(model_version),
                processing_time_ms = VALUES(processing_time_ms),
                timestamp = VALUES(timestamp)
            """,
            (
                detection_id,
                camera_id,
                detections_json,
                risk_level,
                model_version,
                processing_time_ms,
                timestamp,
            ),
        )


def get_detection(detection_id: str) -> dict | None:
    """Lấy một detection theo ID."""
    with get_cursor(commit=False) as cur:
        cur.execute(
            "SELECT * FROM detections WHERE detection_id = %s",
            (detection_id,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return _row_to_detection_response(row)


def list_recent_detections(
    limit: int = 20,
    camera_id: str | None = None,
) -> tuple[list[dict], str | None, bool]:
    """Lấy danh sách detections gần đây, có pagination cursor."""
    with get_cursor(commit=False) as cur:
        if camera_id:
            cur.execute(
                """
                SELECT * FROM detections
                WHERE camera_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (camera_id, limit + 1),
            )
        else:
            cur.execute(
                "SELECT * FROM detections ORDER BY timestamp DESC LIMIT %s",
                (limit + 1,),
            )
        rows = cur.fetchall()

    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor: str | None = None
    if has_more and items:
        last_ts = items[-1]["timestamp"]
        next_cursor = last_ts.isoformat() if hasattr(last_ts, "isoformat") else str(last_ts)

    return ([_row_to_detection_response(r) for r in items], next_cursor, has_more)


# ─────────────────────────────────────────────────────────────────────────────
# Face match operations
# ─────────────────────────────────────────────────────────────────────────────

def insert_face_match(
    match_id: str,
    matched: bool,
    confidence: float,
    threshold: float,
    status: str,
    message: str | None,
    model_version: str,
    processing_time_ms: int,
    trace_id: str | None,
    timestamp: str,
) -> None:
    """Lưu một face match record vào MySQL."""
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO face_matches
                (match_id, matched, confidence, threshold, status, message,
                 model_version, processing_time_ms, trace_id, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                matched = VALUES(matched),
                confidence = VALUES(confidence),
                status = VALUES(status),
                message = VALUES(message)
            """,
            (
                match_id,
                matched,
                confidence,
                threshold,
                status,
                message,
                model_version,
                processing_time_ms,
                trace_id,
                timestamp,
            ),
        )


def get_face_match(match_id: str) -> dict | None:
    """Lấy một face match theo ID."""
    with get_cursor(commit=False) as cur:
        cur.execute(
            "SELECT * FROM face_matches WHERE match_id = %s",
            (match_id,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return _row_to_face_match_response(row)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers: map MySQL row → API response dict
# ─────────────────────────────────────────────────────────────────────────────
# Helpers: map MySQL row → API response dict
# ─────────────────────────────────────────────────────────────────────────────

def to_mysql_datetime(iso_str: str) -> str:
    """Convert ISO 8601 datetime (có hoặc không có Z) → MySQL DATETIME."""
    s = iso_str.replace("Z", "+00:00")
    from datetime import datetime, timezone
    if "+" in s:
        dt = datetime.fromisoformat(s).astimezone(timezone.utc)
    else:
        dt = datetime.fromisoformat(s)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _row_to_detection_response(row: dict) -> dict:
    """Parse MySQL row thành DetectResponse JSON."""
    dets = row["detections"]
    if isinstance(dets, str):
        dets = json.loads(dets)
    items = []
    for d in dets:
        items.append(
            {
                "label": d.get("label"),
                "confidence": d.get("confidence"),
                "bbox": d.get("bbox", {}),
                "class_id": d.get("class_id"),
            }
        )
    ts = row["timestamp"]
    ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
    return {
        "detection_id": row["detection_id"],
        "camera_id": row["camera_id"],
        "detections": items,
        "risk_level": row["risk_level"],
        "model_version": row["model_version"],
        "processing_time_ms": row["processing_time_ms"],
        "timestamp": ts_str,
    }


def _row_to_face_match_response(row: dict) -> dict:
    """Parse MySQL row thành FaceMatchResponse JSON."""
    ts = row["timestamp"]
    ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
    return {
        "match_id": row["match_id"],
        "matched": bool(row["matched"]),
        "confidence": float(row["confidence"]),
        "threshold": float(row["threshold"]),
        "status": row["status"],
        "message": row["message"],
        "model_version": row["model_version"],
        "processing_time_ms": row["processing_time_ms"],
        "trace_id": row["trace_id"],
        "timestamp": ts_str,
    }

