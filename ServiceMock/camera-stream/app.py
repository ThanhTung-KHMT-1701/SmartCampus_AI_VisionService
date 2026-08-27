"""
Camera Stream Mock Service
==========================
Mô phỏng Camera Stream theo hợp đồng chính thức.

Hợp đồng: ServiceMock/camera-stream/camera-stream.openapi.yaml
Endpoints chính (theo contract):
  - GET  /health              Kiểm tra trạng thái (không auth)
  - GET  /cameras            Danh sách camera, lọc theo status
  - GET  /cameras/{cameraId} Chi tiết camera
  - POST /frames             Upload frame ảnh

Flow:
  1. Background worker gửi frames đến AI Vision mỗi STREAM_INTERVAL giây
  2. Các endpoint quản lý camera + frames theo hợp đồng
  3. Camera store + frame store trong memory
"""

import os
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Literal

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
import uvicorn

# ═══════════════════════════════════════════════════════════════════════════
#  Configuration
# ═══════════════════════════════════════════════════════════════════════════

AI_VISION_URL = os.getenv("AI_VISION_URL", "http://ai-vision-gateway:8000")
AI_VISION_TOKEN = os.getenv("AI_VISION_TOKEN", "smartcampus-vision-2026-secure-token")
CAMERA_ID = os.getenv("CAMERA_ID", "cam-entrance-mock-01")
CAMERA_NAME = os.getenv("CAMERA_NAME", "Cổng chính")
CAMERA_LOCATION = os.getenv("CAMERA_LOCATION", "Khu vực cổng chính")
CAMERA_IP = os.getenv("CAMERA_IP", "192.168.1.100")
STREAM_INTERVAL = int(os.getenv("STREAM_INTERVAL", "10"))

# Test images cho simulation
TEST_IMAGES = [
    "https://picsum.photos/640/480?random=1",
    "https://picsum.photos/800/600?random=2",
    "https://picsum.photos/1024/768?random=3",
]

# ═══════════════════════════════════════════════════════════════════════════
#  Logging
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("camera-stream")

# ═══════════════════════════════════════════════════════════════════════════
#  Pydantic Schemas (theo camera-stream.openapi.yaml)
# ═══════════════════════════════════════════════════════════════════════════

CameraStatus = Literal["active", "inactive", "maintenance"]
FrameStatus = Literal["accepted", "rejected"]


class HealthStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ok"]
    service: str
    time: str


class Camera(BaseModel):
    model_config = ConfigDict(extra="forbid")
    camera_id: str
    name: str
    status: CameraStatus
    location: Optional[str] = None
    ip_address: Optional[str] = None
    stream_url: Optional[str] = None


class FrameUploadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    camera_id: str
    image_url: str = Field(..., format="uri")
    motion_detected: bool = False
    timestamp: str = Field(..., format="date-time")
    metadata: Optional[Dict[str, str]] = None


class FrameUploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    frame_id: str
    status: FrameStatus
    message: Optional[str] = None
    timestamp: str


# Internal models (không có trong contract nhưng dùng nội bộ)
class FrameRecord(BaseModel):
    frame_id: str
    camera_id: str
    image_url: str
    motion_detected: bool
    timestamp: str
    metadata: Optional[Dict[str, str]] = None
    detection_id: Optional[str] = None
    detections_count: Optional[int] = None
    risk_level: Optional[str] = None
    processing_time_ms: Optional[int] = None
    success: bool = True
    error: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
#  Application State
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Camera Stream Mock Service",
    version="1.0.0",
    description="Mock theo hợp đồng camera-stream.openapi.yaml",
)

# Camera store
cameras_db: Dict[str, Camera] = {}
_cameras_init = [
    Camera(
        camera_id="cam-gate-01",
        name="Cổng chính",
        status="active",
        location="Khu vực cổng chính",
        ip_address="192.168.1.100",
        stream_url="rtsp://192.168.1.100:554/stream",
    ),
    Camera(
        camera_id="cam-gate-02",
        name="Cổng sau",
        status="active",
        location="Khu vực cổng sau",
        ip_address="192.168.1.101",
        stream_url="rtsp://192.168.1.101:554/stream",
    ),
    Camera(
        camera_id="cam-gate-03",
        name="Cổng phụ",
        status="active",
        location="Khu vực cổng phụ",
        ip_address="192.168.1.102",
        stream_url="rtsp://192.168.1.102:554/stream",
    ),
    Camera(
        camera_id="cam-parking-01",
        name="Bãi đỗ xe A",
        status="active",
        location="Khu vực bãi đỗ xe A",
        ip_address="192.168.1.110",
        stream_url="rtsp://192.168.1.110:554/stream",
    ),
    Camera(
        camera_id="cam-parking-02",
        name="Bãi đỗ xe B",
        status="inactive",
        location="Khu vực bãi đỗ xe B",
        ip_address="192.168.1.111",
        stream_url="rtsp://192.168.1.111:554/stream",
    ),
    Camera(
        camera_id="cam-library-01",
        name="Thư viện tầng 1",
        status="active",
        location="Khu vực thư viện",
        ip_address="192.168.1.120",
        stream_url="rtsp://192.168.1.120:554/stream",
    ),
    Camera(
        camera_id="cam-library-02",
        name="Thư viện tầng 2",
        status="maintenance",
        location="Khu vực thư viện tầng 2",
        ip_address="192.168.1.121",
        stream_url=None,
    ),
    Camera(
        camera_id="cam-entrance-01",
        name="Lối vào chính",
        status="active",
        location="Khu vực lối vào chính",
        ip_address="192.168.1.130",
        stream_url="rtsp://192.168.1.130:554/stream",
    ),
    # Current mock camera (từ env)
    Camera(
        camera_id=CAMERA_ID,
        name=CAMERA_NAME,
        status="active",
        location=CAMERA_LOCATION,
        ip_address=CAMERA_IP,
        stream_url=f"mock://{CAMERA_ID}/stream",
    ),
]
for cam in _cameras_init:
    cameras_db[cam.camera_id] = cam

# Frame store
frames_db: List[FrameRecord] = []
frame_index = 0

# Stream stats
stats = {
    "frames_sent": 0,
    "frames_success": 0,
    "frames_failed": 0,
    "last_frame_at": None,
    "stream_active": False,
}


# ═══════════════════════════════════════════════════════════════════════════
#  Core: Gửi frame đến AI Vision
# ═══════════════════════════════════════════════════════════════════════════

async def send_frame_to_ai_vision(image_url: str, camera_id: str) -> FrameRecord:
    """Gửi 1 frame đến AI Vision Service."""
    global frame_index
    frame_id = f"frame-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    frame_index += 1

    payload = {
        "camera_id": camera_id,
        "image_url": image_url,
        "timestamp": timestamp,
    }
    headers = {
        "Authorization": f"Bearer {AI_VISION_TOKEN}",
        "Content-Type": "application/json",
    }

    logger.info(f"📸 Frame {frame_id[:20]}... -> AI Vision")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{AI_VISION_URL}/vision/detect",
                json=payload,
                headers=headers,
            )
            if response.status_code == 200:
                data = response.json()
                record = FrameRecord(
                    frame_id=frame_id,
                    camera_id=camera_id,
                    image_url=image_url,
                    motion_detected=False,
                    timestamp=timestamp,
                    detection_id=data.get("detection_id"),
                    detections_count=len(data.get("detections", [])),
                    risk_level=data.get("risk_level"),
                    processing_time_ms=data.get("processing_time_ms"),
                    success=True,
                    error=None,
                )
                stats["frames_success"] += 1
                logger.info(f"  ✅ {record.detections_count} objects, risk={record.risk_level}")
            else:
                record = FrameRecord(
                    frame_id=frame_id,
                    camera_id=camera_id,
                    image_url=image_url,
                    motion_detected=False,
                    timestamp=timestamp,
                    success=False,
                    error=f"HTTP {response.status_code}",
                )
                stats["frames_failed"] += 1
                logger.error(f"  ❌ {response.status_code}")
    except Exception as e:
        record = FrameRecord(
            frame_id=frame_id,
            camera_id=camera_id,
            image_url=image_url,
            motion_detected=False,
            timestamp=timestamp,
            success=False,
            error=str(e),
        )
        stats["frames_failed"] += 1
        logger.error(f"  ❌ {e}")

    frames_db.append(record)
    stats["frames_sent"] += 1
    stats["last_frame_at"] = timestamp

    # Giữ tối đa 200 records
    if len(frames_db) > 200:
        frames_db[:] = frames_db[-200:]

    return record


async def stream_worker():
    """Background worker: gửi frames đến AI Vision liên tục."""
    logger.info(f"🎬 Camera Stream started: every {STREAM_INTERVAL}s")
    stats["stream_active"] = True
    image_index = 0

    while stats["stream_active"]:
        image_url = TEST_IMAGES[image_index % len(TEST_IMAGES)]
        image_index += 1
        await send_frame_to_ai_vision(image_url, CAMERA_ID)
        await asyncio.sleep(STREAM_INTERVAL)


# ═══════════════════════════════════════════════════════════════════════════
#  API Endpoints (theo camera-stream.openapi.yaml)
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/health", response_model=HealthStatus)
async def get_health():
    """Không yêu cầu auth."""
    return HealthStatus(
        status="ok",
        service="camera-stream-mock",
        time=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


@app.get("/cameras", response_model=List[Camera])
async def get_cameras(
    status: Optional[str] = Query(
        None,
        enum=["active", "inactive", "all"],
        description="Lọc camera theo trạng thái (mặc định: all)",
    ),
):
    """Danh sách camera. Filter optional theo status."""
    if status is None or status == "all":
        return list(cameras_db.values())
    return [cam for cam in cameras_db.values() if cam.status == status]


@app.get("/cameras/{camera_id}", response_model=Camera)
async def get_camera_by_id(camera_id: str):
    """Chi tiết 1 camera theo camera_id."""
    # Validate pattern theo contract: cam-[a-z0-9-]+
    if not camera_id.startswith("cam-"):
        raise HTTPException(status_code=404, detail="Camera not found")
    if camera_id not in cameras_db:
        raise HTTPException(status_code=404, detail="Camera not found")
    return cameras_db[camera_id]


@app.post("/frames", response_model=FrameUploadResponse, status_code=202)
async def upload_frame(req: FrameUploadRequest):
    """
    Upload frame ảnh. Theo contract trả 202 Accepted.
    Frame được ghi nhận + gửi thẳng đến AI Vision để detect.
    """
    # Tạo frame record
    frame_id = f"frame-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
    timestamp_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    record = FrameRecord(
        frame_id=frame_id,
        camera_id=req.camera_id,
        image_url=req.image_url,
        motion_detected=req.motion_detected,
        timestamp=req.timestamp,
        metadata=req.metadata,
    )

    # Gửi đến AI Vision ngay (trong request này, không blocking dài)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{AI_VISION_URL}/vision/detect",
                json={
                    "camera_id": req.camera_id,
                    "image_url": req.image_url,
                    "timestamp": req.timestamp,
                },
                headers={
                    "Authorization": f"Bearer {AI_VISION_TOKEN}",
                    "Content-Type": "application/json",
                },
            )
            if response.status_code == 200:
                data = response.json()
                record.detection_id = data.get("detection_id")
                record.detections_count = len(data.get("detections", []))
                record.risk_level = data.get("risk_level")
                record.processing_time_ms = data.get("processing_time_ms")
                record.success = True
            else:
                record.success = False
                record.error = f"AI Vision HTTP {response.status_code}"
    except Exception as e:
        record.success = False
        record.error = str(e)

    frames_db.append(record)
    stats["frames_sent"] += 1
    if record.success:
        stats["frames_success"] += 1
    else:
        stats["frames_failed"] += 1

    return FrameUploadResponse(
        frame_id=frame_id,
        status="accepted" if record.success else "rejected",
        message="Frame accepted for processing" if record.success else record.error,
        timestamp=timestamp_iso,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  Debug / Admin endpoints (không có trong contract, để vận hành)
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/frames/history")
async def get_frames_history(limit: int = Query(20, ge=1, le=100)):
    """Lịch sử frames đã gửi đến AI Vision."""
    return {
        "total": len(frames_db),
        "frames": frames_db[-limit:] if frames_db else [],
    }


@app.get("/stats")
async def get_stats():
    """Thống kê stream."""
    sr = (stats["frames_success"] / stats["frames_sent"] * 100) if stats["frames_sent"] > 0 else 0
    return {
        "frames_sent": stats["frames_sent"],
        "frames_success": stats["frames_success"],
        "frames_failed": stats["frames_failed"],
        "success_rate": round(sr, 2),
        "last_frame_at": stats["last_frame_at"],
        "stream_active": stats["stream_active"],
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Startup
# ═══════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 80)
    logger.info("Camera Stream Mock Service starting...")
    logger.info(f"Camera ID: {CAMERA_ID}")
    logger.info(f"AI Vision URL: {AI_VISION_URL}")
    logger.info(f"Stream Interval: {STREAM_INTERVAL}s")
    logger.info(f"Cameras in store: {list(cameras_db.keys())}")
    logger.info("=" * 80)
    asyncio.create_task(stream_worker())


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5000,
        reload=False,
        log_level="info",
    )
