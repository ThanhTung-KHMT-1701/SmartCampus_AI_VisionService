"""MySQL store cho detection và face-match results."""
from __future__ import annotations

import base64
import os
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    Numeric,
    String,
    Text,
    create_engine,
)
from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

if TYPE_CHECKING:
    from .schemas import DetectResponse, FaceMatchResponse

Base = declarative_base()


class DetectionRecord(Base):
    """Bảng lưu trữ detection results."""

    __tablename__ = "detections"

    detection_id = Column(VARCHAR(36), primary_key=True)
    camera_id = Column(VARCHAR(80), nullable=False, index=True)
    detections = Column(Text, nullable=False)
    risk_level = Column(VARCHAR(20), nullable=False)
    model_version = Column(VARCHAR(50), nullable=False)
    processing_time_ms = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_response(self) -> "DetectResponse":
        """Convert record sang Pydantic model."""
        import json
        from .schemas import BoundingBox, Detection, DetectResponse

        detections_data = json.loads(self.detections)
        detections = [
            Detection(
                label=d["label"],
                confidence=d["confidence"],
                bbox=BoundingBox(**d["bbox"]),
                class_id=d.get("class_id"),
            )
            for d in detections_data
        ]
        return DetectResponse(
            detection_id=self.detection_id,
            camera_id=self.camera_id,
            detections=detections,
            risk_level=self.risk_level,
            model_version=self.model_version,
            processing_time_ms=self.processing_time_ms,
            timestamp=self.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )


class FaceMatchRecord(Base):
    """Bảng lưu trữ face match results."""

    __tablename__ = "face_matches"

    match_id = Column(VARCHAR(36), primary_key=True)
    matched = Column(Boolean, nullable=False)
    confidence = Column(Numeric(5, 4), nullable=False)
    threshold = Column(Numeric(5, 4), nullable=False)
    status = Column(VARCHAR(20), nullable=False)
    message = Column(VARCHAR(500), nullable=True)
    model_version = Column(VARCHAR(50), nullable=False)
    processing_time_ms = Column(Integer, nullable=False)
    trace_id = Column(VARCHAR(100), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_response(self) -> "FaceMatchResponse":
        """Convert record sang Pydantic model."""
        from .schemas import FaceMatchResponse

        return FaceMatchResponse(
            match_id=self.match_id,
            matched=self.matched,
            confidence=float(self.confidence),
            threshold=float(self.threshold),
            status=self.status,
            message=self.message,
            model_version=self.model_version,
            processing_time_ms=self.processing_time_ms,
            trace_id=self.trace_id,
            timestamp=self.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )


class DetectionStore:
    """Lưu trữ detection vào MySQL database."""

    _engine = None
    _session_factory = None

    @classmethod
    def _get_engine(cls):
        """Lazy init engine (chạy trong container)."""
        if cls._engine is None:
            host = os.environ.get("MYSQL_HOST", "localhost")
            port = os.environ.get("MYSQL_PORT", "3306")
            user = os.environ.get("MYSQL_USER", "root")
            password = os.environ.get("MYSQL_PASSWORD", "")
            database = os.environ.get("MYSQL_DATABASE", "ai_vision_db")

            connection_string = (
                f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
                "?charset=utf8mb4"
            )
            cls._engine = create_engine(
                connection_string,
                pool_size=5,
                max_overflow=10,
                pool_recycle=3600,
                echo=False,
            )
        return cls._engine

    @classmethod
    def _get_session(cls) -> Session:
        """Get hoặc tạo session factory."""
        if cls._session_factory is None:
            engine = cls._get_engine()
            cls._session_factory = sessionmaker(bind=engine)
            Base.metadata.create_all(engine)
        return cls._session_factory()

    @classmethod
    def init_db(cls):
        """Khởi tạo database (gọi khi app start)."""
        engine = cls._get_engine()
        Base.metadata.create_all(engine)

    @classmethod
    def add(cls, response: "DetectResponse") -> None:
        """Thêm detection record vào database."""
        import json

        session = cls._get_session()
        try:
            detections_json = json.dumps([
                {
                    "label": d.label,
                    "confidence": d.confidence,
                    "bbox": d.bbox.model_dump(),
                    "class_id": d.class_id,
                }
                for d in response.detections
            ])

            record = DetectionRecord(
                detection_id=response.detection_id,
                camera_id=response.camera_id,
                detections=detections_json,
                risk_level=response.risk_level,
                model_version=response.model_version,
                processing_time_ms=response.processing_time_ms,
                timestamp=datetime.strptime(response.timestamp, "%Y-%m-%dT%H:%M:%SZ"),
            )
            session.add(record)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @classmethod
    def get(cls, detection_id: str) -> "DetectResponse | None":
        """Lấy detection theo ID."""
        session = cls._get_session()
        try:
            record = session.query(DetectionRecord).filter_by(detection_id=detection_id).first()
            if record is None:
                return None
            return record.to_response()
        finally:
            session.close()

    @classmethod
    def list_recent(
        cls,
        limit: int,
        camera_id: str | None = None,
    ) -> tuple[list["DetectResponse"], str | None, bool]:
        """Lấy danh sách detection gần đây."""
        session = cls._get_session()
        try:
            query = session.query(DetectionRecord).order_by(DetectionRecord.timestamp.desc())

            if camera_id:
                query = query.filter(DetectionRecord.camera_id == camera_id)

            total_count = query.count()
            records = query.limit(limit + 1).all()

            has_more = len(records) > limit
            items = records[:limit]

            response_items = [r.to_response() for r in items]
            next_cursor = None
            if has_more and items:
                last_timestamp = items[-1].timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
                next_cursor = base64.b64encode(last_timestamp.encode()).decode()

            return response_items, next_cursor, has_more
        finally:
            session.close()


class FaceMatchStore:
    """Lưu trữ face match vào MySQL database."""

    _engine = None
    _session_factory = None

    @classmethod
    def _get_engine(cls):
        """Lazy init engine (chạy trong container)."""
        if cls._engine is None:
            host = os.environ.get("MYSQL_HOST", "localhost")
            port = os.environ.get("MYSQL_PORT", "3306")
            user = os.environ.get("MYSQL_USER", "root")
            password = os.environ.get("MYSQL_PASSWORD", "")
            database = os.environ.get("MYSQL_DATABASE", "ai_vision_db")

            connection_string = (
                f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
                "?charset=utf8mb4"
            )
            cls._engine = create_engine(
                connection_string,
                pool_size=5,
                max_overflow=10,
                pool_recycle=3600,
                echo=False,
            )
        return cls._engine

    @classmethod
    def _get_session(cls) -> Session:
        """Get hoặc tạo session factory."""
        if cls._session_factory is None:
            engine = cls._get_engine()
            cls._session_factory = sessionmaker(bind=engine)
            Base.metadata.create_all(engine)
        return cls._session_factory()

    @classmethod
    def init_db(cls):
        """Khởi tạo database (gọi khi app start)."""
        engine = cls._get_engine()
        Base.metadata.create_all(engine)

    @classmethod
    def add(cls, response: "FaceMatchResponse") -> None:
        """Thêm face match record vào database."""
        session = cls._get_session()
        try:
            record = FaceMatchRecord(
                match_id=response.match_id,
                matched=response.matched,
                confidence=Decimal(str(response.confidence)),
                threshold=Decimal(str(response.threshold)),
                status=response.status,
                message=response.message,
                model_version=response.model_version,
                processing_time_ms=response.processing_time_ms,
                trace_id=response.trace_id,
                timestamp=datetime.strptime(response.timestamp, "%Y-%m-%dT%H:%M:%SZ"),
            )
            session.add(record)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @classmethod
    def get(cls, match_id: str) -> "FaceMatchResponse | None":
        """Lấy face match theo ID."""
        session = cls._get_session()
        try:
            record = session.query(FaceMatchRecord).filter_by(match_id=match_id).first()
            if record is None:
                return None
            return record.to_response()
        finally:
            session.close()

    @classmethod
    def list_recent(cls, limit: int = 100) -> list["FaceMatchResponse"]:
        """Lấy danh sách face match gần đây."""
        session = cls._get_session()
        try:
            records = (
                session.query(FaceMatchRecord)
                .order_by(FaceMatchRecord.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [r.to_response() for r in records]
        finally:
            session.close()
