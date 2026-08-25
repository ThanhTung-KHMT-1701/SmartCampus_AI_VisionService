"""MySQL store cho detection results - thay thế in-memory store."""
from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from typing import Any

import mysql.connector
from mysql.connector import pooling

from .schemas import DetectResponse, Detection, BoundingBox

# Database configuration from environment
DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DATABASE", "ai_vision_db"),
}

# Connection pool settings
POOL_NAME = "ai_vision_pool"
POOL_SIZE = 5

# Global connection pool
_connection_pool: pooling.MySQLConnectionPool | None = None


def _get_pool() -> pooling.MySQLConnectionPool:
    """Get or create the connection pool (singleton)."""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = pooling.MySQLConnectionPool(
            pool_name=POOL_NAME,
            pool_size=POOL_SIZE,
            pool_reset_session=True,
            **DB_CONFIG,
        )
    return _connection_pool


def _get_connection():
    """Get a connection from the pool."""
    return _get_pool().get_connection()


def _parse_detection_data(detection_data: dict) -> Detection:
    """Parse detection data from database to Detection schema."""
    bbox_data = detection_data.get("bbox", {})
    return Detection(
        label=detection_data.get("label", ""),
        confidence=float(detection_data.get("confidence", 0.0)),
        bbox=BoundingBox(
            x=int(bbox_data.get("x", 0)),
            y=int(bbox_data.get("y", 0)),
            width=int(bbox_data.get("width", 0)),
            height=int(bbox_data.get("height", 0)),
        ),
        class_id=int(detection_data.get("class_id", 0)),
    )


def _parse_detections_json(json_str: str) -> list[Detection]:
    """Parse detections JSON from database."""
    try:
        data = json.loads(json_str) if isinstance(json_str, str) else json_str
        return [_parse_detection_data(d) for d in data] if data else []
    except (json.JSONDecodeError, TypeError):
        return []


class DetectionStore:
    """Lưu trữ detection results trong MySQL database."""

    def __init__(self) -> None:
        """Initialize database connection pool."""
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Ensure required tables exist in database."""
        conn = _get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detections (
                    detection_id CHAR(36) PRIMARY KEY,
                    camera_id VARCHAR(80) NOT NULL,
                    detections JSON NOT NULL,
                    risk_level ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL DEFAULT 'LOW',
                    model_version VARCHAR(50) NOT NULL,
                    processing_time_ms INT UNSIGNED NOT NULL,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_camera_id (camera_id),
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_risk_level (risk_level),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def add(self, response: DetectResponse) -> None:
        """Lưu một detection response vào database."""
        conn = _get_connection()
        cursor = conn.cursor()
        try:
            # Convert detections to JSON
            detections_json = json.dumps([
                {
                    "label": d.label,
                    "confidence": d.confidence,
                    "bbox": {
                        "x": d.bbox.x,
                        "y": d.bbox.y,
                        "width": d.bbox.width,
                        "height": d.bbox.height,
                    },
                    "class_id": d.class_id,
                }
                for d in response.detections
            ])

            # Convert timestamp from ISO format (2026-08-25T04:31:50Z) to MySQL format (2026-08-25 04:31:50)
            timestamp_str = response.timestamp.replace("T", " ").replace("Z", "")

            cursor.execute(
                """
                INSERT INTO detections 
                (detection_id, camera_id, detections, risk_level, model_version, processing_time_ms, timestamp)
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
                    response.detection_id,
                    response.camera_id,
                    detections_json,
                    response.risk_level,
                    response.model_version,
                    response.processing_time_ms,
                    timestamp_str,
                ),
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def get(self, detection_id: str) -> DetectResponse | None:
        """Lấy một detection theo ID."""
        conn = _get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM detections WHERE detection_id = %s",
                (detection_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None

            # Convert MySQL datetime to ISO format for response
            db_timestamp = row["timestamp"]
            if isinstance(db_timestamp, datetime):
                response_timestamp = db_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                response_timestamp = str(db_timestamp)

            return DetectResponse(
                detection_id=row["detection_id"],
                camera_id=row["camera_id"],
                detections=_parse_detections_json(row["detections"]),
                risk_level=row["risk_level"],
                model_version=row["model_version"],
                processing_time_ms=row["processing_time_ms"],
                timestamp=response_timestamp,
            )
        finally:
            cursor.close()
            conn.close()

    def list_recent(
        self,
        limit: int,
        camera_id: str | None = None,
        from_time: str | None = None,
        to_time: str | None = None,
    ) -> tuple[list[DetectResponse], str | None, bool]:
        """Lấy danh sách detections gần đây với các bộ lọc."""
        conn = _get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # Build query with filters
            conditions = []
            params = []

            if camera_id:
                conditions.append("camera_id = %s")
                params.append(camera_id)

            if from_time:
                conditions.append("timestamp >= %s")
                params.append(from_time)

            if to_time:
                conditions.append("timestamp <= %s")
                params.append(to_time)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            # Get total count for hasMore calculation
            count_query = f"SELECT COUNT(*) as total FROM detections WHERE {where_clause}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()["total"]

            # Get records
            query = f"""
                SELECT * FROM detections 
                WHERE {where_clause}
                ORDER BY timestamp DESC 
                LIMIT %s
            """
            params.append(limit + 1)  # Get one extra to check hasMore
            cursor.execute(query, params)
            rows = cursor.fetchall()

            has_more = len(rows) > limit
            items = rows[:limit] if has_more else rows

            results = []
            for row in items:
                results.append(
                    DetectResponse(
                        detection_id=row["detection_id"],
                        camera_id=row["camera_id"],
                        detections=_parse_detections_json(row["detections"]),
                        risk_level=row["risk_level"],
                        model_version=row["model_version"],
                        processing_time_ms=row["processing_time_ms"],
                        timestamp=row["timestamp"].strftime("%Y-%m-%dT%H:%M:%SZ") if row["timestamp"] else "",
                    )
                )

            # Generate next cursor
            next_cursor = None
            if has_more and results:
                cursor_data = f"{results[-1].camera_id}:{results[-1].timestamp}"
                next_cursor = base64.b64encode(cursor_data.encode()).decode()

            return results, next_cursor, has_more
        finally:
            cursor.close()
            conn.close()

    def delete_old(self, days_to_keep: int = 30) -> int:
        """Xóa các detection cũ hơn N ngày. Trả về số bản ghi đã xóa."""
        conn = _get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                DELETE FROM detections 
                WHERE timestamp < DATE_SUB(NOW(), INTERVAL %s DAY)
                """,
                (days_to_keep,),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            cursor.close()
            conn.close()

    def count(self) -> int:
        """Đếm tổng số detections trong database."""
        conn = _get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM detections")
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            cursor.close()
            conn.close()
