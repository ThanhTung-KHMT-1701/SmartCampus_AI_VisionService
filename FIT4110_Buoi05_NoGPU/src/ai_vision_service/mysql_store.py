"""MySQL-backed store wrappers cho Gateway service.

Wrapper các hàm từ db.py thành class-based interface tương thích với code cũ.
Gateway service sẽ import DetectionStore và FaceMatchStore từ file này.
"""
from __future__ import annotations

import json
from typing import Any

from . import db
from .schemas import DetectResponse, FaceMatchResponse


class DetectionStore:
    """MySQL-backed detection store."""
    
    @staticmethod
    def init_db() -> None:
        """Initialize database - noop vì schema được tạo bởi migration."""
        # MySQL schema được init bởi container startup hoặc migration script
        pass
    
    @staticmethod
    def add(response: DetectResponse) -> None:
        """Lưu detection response vào MySQL."""
        detections_json = json.dumps([d.model_dump() for d in response.detections])
        db.insert_detection(
            detection_id=response.detection_id,
            camera_id=response.camera_id,
            detections_json=detections_json,
            risk_level=response.risk_level,
            model_version=response.model_version,
            processing_time_ms=response.processing_time_ms,
            timestamp=db.to_mysql_datetime(response.timestamp),
        )
    
    @staticmethod
    def get(detection_id: str) -> DetectResponse | None:
        """Lấy detection theo ID."""
        row = db.get_detection(detection_id)
        if row is None:
            return None
        return DetectResponse(**row)
    
    @staticmethod
    def list_recent(
        limit: int = 20,
        camera_id: str | None = None,
    ) -> tuple[list[DetectResponse], str | None, bool]:
        """List recent detections với pagination."""
        rows, next_cursor, has_more = db.list_recent_detections(
            limit=limit,
            camera_id=camera_id,
        )
        items = [DetectResponse(**row) for row in rows]
        return items, next_cursor, has_more


class FaceMatchStore:
    """MySQL-backed face match store."""
    
    @staticmethod
    def init_db() -> None:
        """Initialize database - noop vì schema được tạo bởi migration."""
        pass
    
    @staticmethod
    def add(response: FaceMatchResponse) -> None:
        """Lưu face match response vào MySQL."""
        db.insert_face_match(
            match_id=response.match_id,
            matched=response.matched,
            confidence=response.confidence,
            threshold=response.threshold,
            status=response.status,
            message=response.message,
            model_version=response.model_version,
            processing_time_ms=response.processing_time_ms,
            trace_id=response.trace_id,
            timestamp=db.to_mysql_datetime(response.timestamp),
        )
    
    @staticmethod
    def get(match_id: str) -> FaceMatchResponse | None:
        """Lấy face match theo ID."""
        row = db.get_face_match(match_id)
        if row is None:
            return None
        return FaceMatchResponse(**row)
