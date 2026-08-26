"""
Camera Stream Mock Service
===========================
Mô phỏng Camera Stream gửi ảnh đến AI Vision Service để detect objects.

Flow:
1. Lấy ảnh từ test URLs hoặc local files
2. Gửi POST request đến AI Vision Service (/vision/detect)
3. Nhận kết quả detection
4. Log kết quả và expose API để xem history
"""

import os
import time
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# ═══════════════════════════════════════════════════════════════════════════
#  Configuration
# ═══════════════════════════════════════════════════════════════════════════

AI_VISION_URL = os.getenv("AI_VISION_URL", "http://ai-vision-gateway:8000")
AI_VISION_TOKEN = os.getenv("AI_VISION_TOKEN", "smartcampus-vision-2026-secure-token")
CAMERA_ID = os.getenv("CAMERA_ID", "cam-entrance-mock-01")
STREAM_INTERVAL = int(os.getenv("STREAM_INTERVAL", "10"))  # seconds

# Test images
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
#  Data Models
# ═══════════════════════════════════════════════════════════════════════════

class StreamStatus(BaseModel):
    status: str = "running"
    camera_id: str
    ai_vision_url: str
    frames_sent: int = 0
    last_frame_at: Optional[str] = None
    stream_interval: int

class FrameHistory(BaseModel):
    frame_id: str
    camera_id: str
    image_url: str
    sent_at: str
    detection_id: Optional[str] = None
    detections_count: Optional[int] = None
    risk_level: Optional[str] = None
    processing_time_ms: Optional[int] = None
    success: bool
    error: Optional[str] = None

# ═══════════════════════════════════════════════════════════════════════════
#  Application State
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Camera Stream Mock Service",
    version="1.0.0",
    description="Mock service mô phỏng camera gửi frames đến AI Vision"
)

# In-memory storage
frame_history: List[FrameHistory] = []
stats = {
    "frames_sent": 0,
    "frames_success": 0,
    "frames_failed": 0,
    "last_frame_at": None,
    "stream_active": False
}

# ═══════════════════════════════════════════════════════════════════════════
#  Core Functions
# ═══════════════════════════════════════════════════════════════════════════

async def send_frame_to_ai_vision(image_url: str) -> FrameHistory:
    """Gửi 1 frame đến AI Vision Service"""
    frame_id = str(uuid.uuid4())
    sent_at = datetime.now(timezone.utc).isoformat()
    
    payload = {
        "camera_id": CAMERA_ID,
        "image_url": image_url,
        "timestamp": sent_at
    }
    
    headers = {
        "Authorization": f"Bearer {AI_VISION_TOKEN}",
        "Content-Type": "application/json"
    }
    
    logger.info(f"📸 Sending frame {frame_id[:8]}... to AI Vision: {image_url}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{AI_VISION_URL}/vision/detect",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                history = FrameHistory(
                    frame_id=frame_id,
                    camera_id=CAMERA_ID,
                    image_url=image_url,
                    sent_at=sent_at,
                    detection_id=data.get("detection_id"),
                    detections_count=len(data.get("detections", [])),
                    risk_level=data.get("risk_level"),
                    processing_time_ms=data.get("processing_time_ms"),
                    success=True,
                    error=None
                )
                stats["frames_success"] += 1
                logger.info(f"✅ Frame {frame_id[:8]}... processed: {history.detections_count} objects, risk={history.risk_level}")
                return history
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                history = FrameHistory(
                    frame_id=frame_id,
                    camera_id=CAMERA_ID,
                    image_url=image_url,
                    sent_at=sent_at,
                    success=False,
                    error=error_msg
                )
                stats["frames_failed"] += 1
                logger.error(f"❌ Frame {frame_id[:8]}... failed: {error_msg}")
                return history
                
    except Exception as e:
        error_msg = str(e)
        history = FrameHistory(
            frame_id=frame_id,
            camera_id=CAMERA_ID,
            image_url=image_url,
            sent_at=sent_at,
            success=False,
            error=error_msg
        )
        stats["frames_failed"] += 1
        logger.error(f"❌ Frame {frame_id[:8]}... error: {error_msg}")
        return history

async def stream_worker():
    """Background worker: gửi frames liên tục"""
    logger.info(f"🎬 Camera Stream started: sending frames every {STREAM_INTERVAL}s")
    stats["stream_active"] = True
    
    image_index = 0
    while stats["stream_active"]:
        try:
            # Lấy ảnh từ danh sách test images (rotate)
            image_url = TEST_IMAGES[image_index % len(TEST_IMAGES)]
            image_index += 1
            
            # Gửi frame
            history = await send_frame_to_ai_vision(image_url)
            frame_history.append(history)
            
            # Update stats
            stats["frames_sent"] += 1
            stats["last_frame_at"] = datetime.now(timezone.utc).isoformat()
            
            # Giữ tối đa 100 frames trong history
            if len(frame_history) > 100:
                frame_history.pop(0)
            
            # Wait trước khi gửi frame tiếp theo
            await asyncio.sleep(STREAM_INTERVAL)
            
        except Exception as e:
            logger.error(f"Stream worker error: {e}")
            await asyncio.sleep(5)  # Retry sau 5s nếu lỗi

# ═══════════════════════════════════════════════════════════════════════════
#  API Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "camera-stream-mock",
        "version": "1.0.0",
        "stream_active": stats["stream_active"],
        "ai_vision_url": AI_VISION_URL
    }

@app.get("/status", response_model=StreamStatus)
async def get_status():
    """Lấy trạng thái stream hiện tại"""
    return StreamStatus(
        status="running" if stats["stream_active"] else "stopped",
        camera_id=CAMERA_ID,
        ai_vision_url=AI_VISION_URL,
        frames_sent=stats["frames_sent"],
        last_frame_at=stats["last_frame_at"],
        stream_interval=STREAM_INTERVAL
    )

@app.get("/frames/history")
async def get_frame_history(limit: int = 20):
    """Lấy lịch sử frames đã gửi"""
    return {
        "total": len(frame_history),
        "limit": limit,
        "frames": frame_history[-limit:] if frame_history else []
    }

@app.get("/stats")
async def get_stats():
    """Lấy thống kê"""
    success_rate = (stats["frames_success"] / stats["frames_sent"] * 100) if stats["frames_sent"] > 0 else 0
    return {
        "frames_sent": stats["frames_sent"],
        "frames_success": stats["frames_success"],
        "frames_failed": stats["frames_failed"],
        "success_rate": round(success_rate, 2),
        "last_frame_at": stats["last_frame_at"],
        "stream_active": stats["stream_active"]
    }

@app.post("/stream/start")
async def start_stream(background_tasks: BackgroundTasks):
    """Bắt đầu stream (tự động chạy khi service start)"""
    if stats["stream_active"]:
        return {"message": "Stream already running"}
    
    stats["stream_active"] = True
    background_tasks.add_task(stream_worker)
    return {"message": "Stream started", "interval": STREAM_INTERVAL}

@app.post("/stream/stop")
async def stop_stream():
    """Dừng stream"""
    stats["stream_active"] = False
    return {"message": "Stream stopped"}

@app.post("/frames/send")
async def send_single_frame(image_url: Optional[str] = None):
    """Gửi 1 frame riêng lẻ (manual test)"""
    if not image_url:
        image_url = TEST_IMAGES[0]
    
    history = await send_frame_to_ai_vision(image_url)
    frame_history.append(history)
    stats["frames_sent"] += 1
    stats["last_frame_at"] = datetime.now(timezone.utc).isoformat()
    
    return history

# ═══════════════════════════════════════════════════════════════════════════
#  Startup
# ═══════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Auto-start stream khi service khởi động"""
    logger.info("=" * 80)
    logger.info("Camera Stream Mock Service starting...")
    logger.info(f"Camera ID: {CAMERA_ID}")
    logger.info(f"AI Vision URL: {AI_VISION_URL}")
    logger.info(f"Stream Interval: {STREAM_INTERVAL}s")
    logger.info("=" * 80)
    
    # Auto-start stream
    asyncio.create_task(stream_worker())

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5000,
        reload=False,
        log_level="info"
    )
