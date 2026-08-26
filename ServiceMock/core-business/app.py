"""
Core Business Mock Service
===========================
Mô phỏng Core Business Service nhận và xử lý kết quả detection từ AI Vision.

Flow:
1. Expose API để AI Vision hoặc các service khác query kết quả
2. Poll AI Vision Service để lấy recent detections
3. Xử lý business logic dựa trên risk_level
4. Log và expose dashboard
"""

import os
import time
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from enum import Enum

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# ═══════════════════════════════════════════════════════════════════════════
#  Configuration
# ═══════════════════════════════════════════════════════════════════════════

AI_VISION_URL = os.getenv("AI_VISION_URL", "http://ai-vision-gateway:8000")
AI_VISION_TOKEN = os.getenv("AI_VISION_TOKEN", "smartcampus-vision-2026-secure-token")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "15"))  # seconds

# ═══════════════════════════════════════════════════════════════════════════
#  Logging
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("core-business")

# ═══════════════════════════════════════════════════════════════════════════
#  Data Models
# ═══════════════════════════════════════════════════════════════════════════

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ActionType(str, Enum):
    NONE = "NONE"
    LOG = "LOG"
    ALERT = "ALERT"
    ESCALATE = "ESCALATE"

class DetectionRecord(BaseModel):
    detection_id: str
    camera_id: str
    detections_count: int
    risk_level: RiskLevel
    model_version: str
    timestamp: str
    received_at: str
    action_taken: ActionType
    notes: Optional[str] = None

class BusinessMetrics(BaseModel):
    total_detections: int
    by_risk_level: Dict[str, int]
    by_action: Dict[str, int]
    last_poll_at: Optional[str]
    poll_active: bool

# ═══════════════════════════════════════════════════════════════════════════
#  Application State
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Core Business Mock Service",
    version="1.0.0",
    description="Mock service mô phỏng Core Business nhận kết quả từ AI Vision"
)

# In-memory storage
detection_records: List[DetectionRecord] = []
stats = {
    "total_detections": 0,
    "risk_level_counts": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
    "action_counts": {"NONE": 0, "LOG": 0, "ALERT": 0, "ESCALATE": 0},
    "last_poll_at": None,
    "poll_active": False,
    "last_cursor": None
}

# ═══════════════════════════════════════════════════════════════════════════
#  Business Logic
# ═══════════════════════════════════════════════════════════════════════════

def determine_action(risk_level: RiskLevel, detections_count: int) -> ActionType:
    """Xác định hành động dựa trên risk level và số lượng objects"""
    if risk_level == RiskLevel.CRITICAL:
        return ActionType.ESCALATE
    elif risk_level == RiskLevel.HIGH:
        return ActionType.ALERT
    elif risk_level == RiskLevel.MEDIUM and detections_count > 5:
        return ActionType.ALERT
    elif risk_level == RiskLevel.LOW and detections_count > 0:
        return ActionType.LOG
    else:
        return ActionType.NONE

def process_detection(detection_data: Dict[str, Any]) -> DetectionRecord:
    """Xử lý 1 detection result từ AI Vision"""
    detection_id = detection_data.get("detection_id")
    camera_id = detection_data.get("camera_id")
    detections = detection_data.get("detections", [])
    risk_level = RiskLevel(detection_data.get("risk_level", "LOW"))
    model_version = detection_data.get("model_version", "unknown")
    timestamp = detection_data.get("timestamp")
    
    # Business logic: quyết định action
    action = determine_action(risk_level, len(detections))
    
    # Tạo notes dựa trên action
    notes = None
    if action == ActionType.ESCALATE:
        notes = f"⚠️ CRITICAL: {len(detections)} objects detected with HIGH risk - Security team notified"
    elif action == ActionType.ALERT:
        notes = f"🔔 ALERT: {len(detections)} objects detected - Monitoring team notified"
    elif action == ActionType.LOG:
        notes = f"📝 LOG: {len(detections)} objects detected - Normal activity"
    
    record = DetectionRecord(
        detection_id=detection_id,
        camera_id=camera_id,
        detections_count=len(detections),
        risk_level=risk_level,
        model_version=model_version,
        timestamp=timestamp,
        received_at=datetime.now(timezone.utc).isoformat(),
        action_taken=action,
        notes=notes
    )
    
    return record

# ═══════════════════════════════════════════════════════════════════════════
#  Core Functions
# ═══════════════════════════════════════════════════════════════════════════

async def poll_ai_vision():
    """Poll AI Vision Service để lấy recent detections"""
    headers = {
        "Authorization": f"Bearer {AI_VISION_TOKEN}",
        "Content-Type": "application/json"
    }
    
    params = {
        "limit": 10
    }
    
    # Nếu có cursor từ lần poll trước, dùng nó để tiếp tục
    if stats["last_cursor"]:
        params["cursor"] = stats["last_cursor"]
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{AI_VISION_URL}/vision/results/recent",
                params=params,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                has_more = data.get("hasMore", False)
                next_cursor = data.get("nextCursor")
                
                logger.info(f"📥 Polled AI Vision: {len(items)} new detections, hasMore={has_more}")
                
                # Process mỗi detection
                for item in items:
                    record = process_detection(item)
                    detection_records.append(record)
                    
                    # Update stats
                    stats["total_detections"] += 1
                    stats["risk_level_counts"][record.risk_level.value] += 1
                    stats["action_counts"][record.action_taken.value] += 1
                    
                    logger.info(f"  ✓ {record.detection_id[:8]}... | {record.camera_id} | Risk={record.risk_level.value} | Action={record.action_taken.value}")
                
                # Update cursor cho lần poll tiếp theo
                stats["last_cursor"] = next_cursor
                stats["last_poll_at"] = datetime.now(timezone.utc).isoformat()
                
                # Giữ tối đa 200 records trong memory
                if len(detection_records) > 200:
                    detection_records[:] = detection_records[-200:]
                
                return len(items)
            else:
                logger.error(f"❌ Poll failed: HTTP {response.status_code}")
                return 0
                
    except Exception as e:
        logger.error(f"❌ Poll error: {e}")
        return 0

async def poll_worker():
    """Background worker: poll AI Vision liên tục"""
    logger.info(f"🔄 Core Business polling started: every {POLL_INTERVAL}s")
    stats["poll_active"] = True
    
    while stats["poll_active"]:
        try:
            await poll_ai_vision()
            await asyncio.sleep(POLL_INTERVAL)
        except Exception as e:
            logger.error(f"Poll worker error: {e}")
            await asyncio.sleep(5)

# ═══════════════════════════════════════════════════════════════════════════
#  API Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "core-business-mock",
        "version": "1.0.0",
        "poll_active": stats["poll_active"],
        "ai_vision_url": AI_VISION_URL
    }

@app.get("/detections")
async def get_detections(
    limit: int = Query(20, ge=1, le=100),
    risk_level: Optional[RiskLevel] = None,
    camera_id: Optional[str] = None
):
    """Lấy danh sách detections đã xử lý"""
    filtered = detection_records
    
    # Filter by risk_level
    if risk_level:
        filtered = [r for r in filtered if r.risk_level == risk_level]
    
    # Filter by camera_id
    if camera_id:
        filtered = [r for r in filtered if r.camera_id == camera_id]
    
    return {
        "total": len(filtered),
        "limit": limit,
        "filters": {
            "risk_level": risk_level.value if risk_level else None,
            "camera_id": camera_id
        },
        "detections": filtered[-limit:] if filtered else []
    }

@app.get("/detections/{detection_id}")
async def get_detection_by_id(detection_id: str):
    """Lấy chi tiết 1 detection"""
    for record in detection_records:
        if record.detection_id == detection_id:
            return record
    
    raise HTTPException(status_code=404, detail="Detection not found")

@app.get("/metrics", response_model=BusinessMetrics)
async def get_metrics():
    """Lấy business metrics"""
    return BusinessMetrics(
        total_detections=stats["total_detections"],
        by_risk_level=stats["risk_level_counts"],
        by_action=stats["action_counts"],
        last_poll_at=stats["last_poll_at"],
        poll_active=stats["poll_active"]
    )

@app.get("/dashboard")
async def get_dashboard():
    """Dashboard với thống kê tổng quan"""
    return {
        "service": "Core Business Mock",
        "status": "operational" if stats["poll_active"] else "paused",
        "ai_vision_url": AI_VISION_URL,
        "poll_interval": POLL_INTERVAL,
        "statistics": {
            "total_detections": stats["total_detections"],
            "by_risk_level": stats["risk_level_counts"],
            "by_action_taken": stats["action_counts"],
            "last_poll": stats["last_poll_at"]
        },
        "recent_detections": detection_records[-10:] if detection_records else []
    }

@app.post("/poll/start")
async def start_polling(background_tasks):
    """Bắt đầu polling (tự động chạy khi service start)"""
    if stats["poll_active"]:
        return {"message": "Polling already active"}
    
    stats["poll_active"] = True
    background_tasks.add_task(poll_worker)
    return {"message": "Polling started", "interval": POLL_INTERVAL}

@app.post("/poll/stop")
async def stop_polling():
    """Dừng polling"""
    stats["poll_active"] = False
    return {"message": "Polling stopped"}

@app.post("/poll/now")
async def poll_now():
    """Trigger 1 lần poll ngay lập tức"""
    count = await poll_ai_vision()
    return {"message": f"Polled {count} new detections"}

# ═══════════════════════════════════════════════════════════════════════════
#  Startup
# ═══════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Auto-start polling khi service khởi động"""
    logger.info("=" * 80)
    logger.info("Core Business Mock Service starting...")
    logger.info(f"AI Vision URL: {AI_VISION_URL}")
    logger.info(f"Poll Interval: {POLL_INTERVAL}s")
    logger.info("=" * 80)
    
    # Auto-start polling
    asyncio.create_task(poll_worker())

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=6000,
        reload=False,
        log_level="info"
    )
