"""
Core Business Mock Service
===========================
Mô phỏng Core Business Service theo hợp đồng chính thức.

Hợp đồng: ServiceMock/core-business/core-business.openapi.yaml
Endpoints chính:
  - GET  /health
  - POST /alerts                        Tạo cảnh báo
  - GET  /alerts                        Danh sách có pagination
  - GET  /alerts/recent                 Cảnh báo gần đây
  - GET  /alerts/{alertId}              Chi tiết
  - POST /events                        Sensor/Access event
  - POST /access/check                  Check policy ra/vào realtime
  - GET  /policies/access/{policyId}    Lấy policy
  - GET  /decisions/{decisionId}        Audit decision
  - POST /vision/detection-result       Nhận kết quả từ AI Vision webhook

Flow:
  1. Background poll AI Vision mỗi POLL_INTERVAL giây
  2. Mỗi detection từ AI Vision -> tạo Alert + push vào in-memory store
  3. Risk HIGH/CRITICAL -> alertType=UNKNOWN_PERSON
  4. Risk MEDIUM         -> alertType=SYSTEM_ERROR
  5. Risk LOW            -> không tạo alert (chỉ log)
"""

import os
import time
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Literal
from enum import Enum

import httpx
from fastapi import FastAPI, HTTPException, Query, Header, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
import uvicorn

# ═══════════════════════════════════════════════════════════════════════════
#  Configuration
# ═══════════════════════════════════════════════════════════════════════════

AI_VISION_URL = os.getenv("AI_VISION_URL", "http://ai-vision-gateway:8000")
AI_VISION_TOKEN = os.getenv("AI_VISION_TOKEN", "smartcampus-vision-2026-secure-token")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "15"))
# Bearer token consumer gọi Core Business (đối tác cung cấp, mặc định lab)
CORE_BUSINESS_TOKEN = os.getenv("CORE_BUSINESS_TOKEN", "local-dev-token-vision")

# ═══════════════════════════════════════════════════════════════════════════
#  Logging
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("core-business")

# ═══════════════════════════════════════════════════════════════════════════
#  Constants from OpenAPI contract
# ═══════════════════════════════════════════════════════════════════════════

AlertSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
AlertType = Literal[
    "UNAUTHORIZED_ACCESS",
    "SENSOR_THRESHOLD_EXCEEDED",
    "UNKNOWN_PERSON",
    "SYSTEM_ERROR",
    "AI_VISION_DETECTION",
    "SUSPICIOUS_OBJECT",
]
AlertStatus = Literal["OPEN", "ACKNOWLEDGED", "RESOLVED"]


# ═══════════════════════════════════════════════════════════════════════════
#  Pydantic Schemas (theo core-business.openapi.yaml)
# ═══════════════════════════════════════════════════════════════════════════

class HealthStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ok"]
    service: str
    time: str


class CreateAlertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sourceService: str = Field(..., min_length=2, max_length=80, pattern=r"^[a-z0-9-]+$")
    alertType: AlertType
    severity: AlertSeverity
    message: str = Field(..., min_length=5, max_length=500)
    relatedEventId: Optional[str] = Field(None)


class Alert(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    sourceService: str
    alertType: AlertType
    severity: AlertSeverity
    message: str
    relatedEventId: Optional[str] = None
    status: AlertStatus = "OPEN"
    createdAt: str
    resolvedAt: Optional[str] = None


class AlertPage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: List[Alert]
    nextCursor: Optional[str] = None
    hasMore: bool


class RecentAlertsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: List[Alert]


class EventAccepted(BaseModel):
    model_config = ConfigDict(extra="forbid")
    eventId: str
    acceptedAt: str


class SensorEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    eventType: Literal["sensor.reading.created", "sensor.threshold.exceeded"]
    eventId: str
    occurredAt: str
    correlationId: str
    source: Literal["iot-ingestion"]
    deviceId: str = Field(..., pattern=r"^SENSOR-[0-9]{3}$")
    metric: Literal["temperature", "humidity", "smoke", "motion"]
    value: float = Field(..., ge=-100, le=1000)
    unit: str = Field(..., min_length=1, max_length=20)
    locationId: str


class AccessEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    eventType: Literal["ACCESS_CHECK"]
    eventId: str
    gateId: str = Field(..., pattern=r"^GATE-[0-9]{2}$")
    cardId: str = Field(..., pattern=r"^RFID-[0-9]{4}-[0-9]{3}$")
    decision: Literal["ALLOW", "DENY"]
    timestamp: str


class AccessCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cardId: str = Field(..., pattern=r"^RFID-[0-9]{4}-[0-9]{3}$")
    gateId: str = Field(..., pattern=r"^GATE-[0-9]{2}$")
    direction: Literal["IN", "OUT"]
    idempotencyKey: str
    timestamp: str


class AccessDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decisionId: str
    cardId: str
    gateId: str
    result: Literal["ALLOW", "DENY"]
    reasonCode: Literal[
        "VALID_CARD", "EXPIRED_CARD", "BLACKLISTED",
        "OUTSIDE_TIME_WINDOW", "UNKNOWN_CARD", "POLICY_DENY",
    ]
    policyId: Optional[str] = None
    evaluatedAt: str
    expiresAt: Optional[str] = None


class AccessPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    policyId: str = Field(..., pattern=r"^POL-[0-9]{3}$")
    name: str = Field(..., min_length=3, max_length=120)
    effect: Literal["ALLOW", "DENY"]
    status: Literal["ACTIVE", "INACTIVE"]
    description: Optional[str] = Field(None, max_length=500)
    timeWindow: Optional[Dict[str, str]] = None
    allowedGates: Optional[List[str]] = None


class BoundingBox(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    width: int = Field(..., ge=1)
    height: int = Field(..., ge=1)


class Detection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: BoundingBox
    class_id: int


class AIVisionDetectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    detection_id: str
    camera_id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    detections: List[Detection]
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    model_version: str
    processing_time_ms: Optional[int] = None
    timestamp: str
    trace_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AIVisionResultAck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ack_id: str
    detection_id: str
    status: Literal["ACCEPTED", "REJECTED", "PROCESSING"]
    action_taken: str
    alert_id: Optional[str] = None
    message: str
    processed_at: str


# ═══════════════════════════════════════════════════════════════════════════
#  Application State
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Core Business Mock Service",
    version="1.0.0",
    description="Mock theo hợp đồng core-business.openapi.yaml",
)

# In-memory stores
alerts_store: List[Alert] = []
events_log: List[Dict[str, Any]] = []
decisions_store: Dict[str, AccessDecision] = {}
idempotency_keys: set = set()

stats = {
    "total_detections": 0,
    "risk_level_counts": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
    "alert_counts": {"OPEN": 0, "ACKNOWLEDGED": 0, "RESOLVED": 0},
    "last_poll_at": None,
    "poll_active": False,
    "last_cursor": None,
}

# ═══════════════════════════════════════════════════════════════════════════
#  Auth dependency (Bearer token)
# ═══════════════════════════════════════════════════════════════════════════

def require_bearer(authorization: Optional[str] = Header(None)) -> None:
    """Verify Bearer token trừ khi path là /health."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail="Thiếu Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    if token != CORE_BUSINESS_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Token không hợp lệ",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ═══════════════════════════════════════════════════════════════════════════
#  Business Logic: AI Vision -> Alert mapping
# ═══════════════════════════════════════════════════════════════════════════

def risk_to_alert_type(risk_level: str) -> AlertType:
    """Theo hợp đồng, AI Vision risk level map sang AlertType enum."""
    mapping = {
        "CRITICAL": "UNAUTHORIZED_ACCESS",
        "HIGH": "UNKNOWN_PERSON",
        "MEDIUM": "SYSTEM_ERROR",
        "LOW": "SYSTEM_ERROR",
    }
    return mapping.get(risk_level, "SYSTEM_ERROR")


def detection_to_alert(detection: Dict[str, Any]) -> Optional[Alert]:
    """
    Tạo Alert từ AI Vision detection.
    Chỉ tạo alert khi risk >= MEDIUM (LOW bỏ qua để giảm noise).
    """
    risk = detection.get("risk_level", "LOW")
    if risk == "LOW":
        return None

    detection_id = detection.get("detection_id", str(uuid.uuid4()))
    camera_id = detection.get("camera_id", "unknown")
    detections = detection.get("detections", [])
    n = len(detections)

    message = (
        f"Phát hiện {n} đối tượng tại camera {camera_id} "
        f"với mức rủi ro {risk}"
    )

    return Alert(
        id=detection_id,
        sourceService="ai-vision-gateway",
        alertType=risk_to_alert_type(risk),
        severity=risk,
        message=message,
        relatedEventId=detection_id,
        status="OPEN",
        createdAt=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        resolvedAt=None,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  Core Functions
# ═══════════════════════════════════════════════════════════════════════════

async def poll_ai_vision():
    """Poll AI Vision Service để lấy recent detections, sau đó sinh Alert."""
    headers = {
        "Authorization": f"Bearer {AI_VISION_TOKEN}",
        "Content-Type": "application/json",
    }
    params: Dict[str, Any] = {"limit": 10}
    if stats["last_cursor"]:
        params["cursor"] = stats["last_cursor"]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{AI_VISION_URL}/vision/results/recent",
                params=params,
                headers=headers,
            )
            if response.status_code != 200:
                logger.error(f"❌ Poll failed: HTTP {response.status_code}")
                return 0

            data = response.json()
            items = data.get("items", [])
            has_more = data.get("hasMore", False)
            next_cursor = data.get("nextCursor")

            logger.info(f"📥 Polled AI Vision: {len(items)} detections, hasMore={has_more}")

            for item in items:
                stats["total_detections"] += 1
                risk = item.get("risk_level", "LOW")
                if risk in stats["risk_level_counts"]:
                    stats["risk_level_counts"][risk] += 1

                alert = detection_to_alert(item)
                if alert:
                    alerts_store.append(alert)
                    stats["alert_counts"][alert.status] += 1
                    logger.info(
                        f"  🚨 Alert {alert.id[:8]}... | {alert.alertType} | "
                        f"Severity={alert.severity} | status={alert.status}"
                    )
                else:
                    logger.info(
                        f"  📝 LOG only | {item.get('camera_id')} | Risk={risk}"
                    )

            stats["last_cursor"] = next_cursor
            stats["last_poll_at"] = datetime.now(timezone.utc).isoformat()

            # Giữ tối đa 500 alerts trong memory
            if len(alerts_store) > 500:
                alerts_store[:] = alerts_store[-500:]
            return len(items)

    except Exception as e:
        logger.error(f"❌ Poll error: {e}")
        return 0


async def poll_worker():
    """Background worker: poll AI Vision liên tục."""
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
#  API Endpoints (theo core-business.openapi.yaml)
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/health", response_model=HealthStatus)
async def get_health():
    """Không yêu cầu auth."""
    return HealthStatus(
        status="ok",
        service="core-business-mock",
        time=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


# ── /alerts ────────────────────────────────────────────────────────────────

@app.post("/alerts", response_model=Alert, status_code=201)
async def create_alert(req: CreateAlertRequest, authorization: Optional[str] = Header(None)):
    """Tạo cảnh báo mới."""
    require_bearer(authorization)
    alert = Alert(
        id=str(uuid.uuid4()),
        sourceService=req.sourceService,
        alertType=req.alertType,
        severity=req.severity,
        message=req.message,
        relatedEventId=req.relatedEventId,
        status="OPEN",
        createdAt=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        resolvedAt=None,
    )
    alerts_store.append(alert)
    stats["alert_counts"][alert.status] = stats["alert_counts"].get(alert.status, 0) + 1
    logger.info(f"➕ Alert created: {alert.id[:8]}... | {alert.alertType}")
    return alert


@app.get("/alerts", response_model=AlertPage)
async def list_alerts(
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    authorization: Optional[str] = Header(None),
):
    """Danh sách cảnh báo có cursor pagination."""
    require_bearer(authorization)
    # Decode cursor (đơn giản: số thứ tự)
    start = 0
    if cursor:
        try:
            start = int(cursor)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cursor")

    end = start + limit
    page_items = alerts_store[start:end]
    next_cursor = str(end) if end < len(alerts_store) else None
    return AlertPage(
        items=page_items,
        nextCursor=next_cursor,
        hasMore=end < len(alerts_store),
    )


@app.get("/alerts/recent", response_model=RecentAlertsResponse)
async def get_recent_alerts(
    limit: int = Query(20, ge=1, le=100),
    authorization: Optional[str] = Header(None),
):
    """Lấy các cảnh báo gần đây (mới nhất trước)."""
    require_bearer(authorization)
    # Lấy N alert mới nhất
    recent = alerts_store[-limit:] if alerts_store else []
    recent.reverse()
    return RecentAlertsResponse(items=recent)


@app.get("/alerts/{alert_id}", response_model=Alert)
async def get_alert_by_id(
    alert_id: str,
    authorization: Optional[str] = Header(None),
):
    require_bearer(authorization)
    for a in alerts_store:
        if a.id == alert_id:
            return a
    raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")


# ── /events ────────────────────────────────────────────────────────────────

@app.post("/events", response_model=EventAccepted, status_code=201)
async def create_event(
    payload: Dict[str, Any],
    authorization: Optional[str] = Header(None),
):
    """Nhận event (Sensor hoặc Access)."""
    require_bearer(authorization)
    event_type = payload.get("eventType")
    if event_type not in ("sensor.reading.created", "sensor.threshold.exceeded", "ACCESS_CHECK"):
        raise HTTPException(status_code=422, detail=f"Unsupported eventType: {event_type}")

    event_id = payload.get("eventId") or str(uuid.uuid4())
    events_log.append(payload)
    logger.info(f"📥 Event received: {event_type} | {event_id[:8]}...")
    return EventAccepted(
        eventId=event_id,
        acceptedAt=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


# ── /access/check ─────────────────────────────────────────────────────────

@app.post("/access/check", response_model=AccessDecision)
async def check_access_policy(
    req: AccessCheckRequest,
    authorization: Optional[str] = Header(None),
):
    """Check policy ra/vào - phản hồi trong ≤200ms (mock)."""
    require_bearer(authorization)

    # Idempotency check
    if req.idempotencyKey in idempotency_keys:
        raise HTTPException(status_code=409, detail="Duplicate idempotencyKey")
    idempotency_keys.add(req.idempotencyKey)

    # Mock policy: cho phép hết, trừ cardId chứa "DENY"
    if "DENY" in req.cardId.upper():
        decision = AccessDecision(
            decisionId=str(uuid.uuid4()),
            cardId=req.cardId,
            gateId=req.gateId,
            result="DENY",
            reasonCode="BLACKLISTED",
            policyId="POL-002",
            evaluatedAt=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            expiresAt=None,
        )
    else:
        decision = AccessDecision(
            decisionId=str(uuid.uuid4()),
            cardId=req.cardId,
            gateId=req.gateId,
            result="ALLOW",
            reasonCode="VALID_CARD",
            policyId="POL-001",
            evaluatedAt=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            expiresAt=None,
        )

    decisions_store[decision.decisionId] = decision
    logger.info(f"🚪 Access {req.cardId} @ {req.gateId} -> {decision.result}")
    return decision


# ── /policies/access/{policyId} ────────────────────────────────────────────

@app.get("/policies/access/{policy_id}", response_model=AccessPolicy)
async def get_access_policy(
    policy_id: str,
    authorization: Optional[str] = Header(None),
):
    require_bearer(authorization)
    if not policy_id.startswith("POL-"):
        raise HTTPException(status_code=404, detail="Policy not found")
    return AccessPolicy(
        policyId=policy_id,
        name="Giờ hành chính cổng chính" if policy_id == "POL-001" else f"Policy {policy_id}",
        effect="ALLOW",
        status="ACTIVE",
        description="Cho phép truy cập cổng chính từ 7:00-22:00",
        timeWindow={"start": "07:00", "end": "22:00"},
        allowedGates=["GATE-01", "GATE-02"],
    )


# ── /decisions/{decisionId} ───────────────────────────────────────────────

@app.get("/decisions/{decision_id}", response_model=AccessDecision)
async def get_decision_by_id(
    decision_id: str,
    authorization: Optional[str] = Header(None),
):
    require_bearer(authorization)
    if decision_id not in decisions_store:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decisions_store[decision_id]


# ── /vision/detection-result ──────────────────────────────────────────────

@app.post("/vision/detection-result", response_model=AIVisionResultAck)
async def receive_ai_vision_detection(
    payload: AIVisionDetectionResult,
    authorization: Optional[str] = Header(None),
):
    """
    Webhook endpoint: AI Vision Service gửi kết quả detection.
    Core Business nhận, áp dụng rule, tạo alert nếu cần.
    """
    require_bearer(authorization)
    
    detection_id = payload.detection_id
    camera_id = payload.camera_id
    risk_level = payload.risk_level
    n_detections = len(payload.detections)
    
    logger.info(
        f"📥 AI Vision Detection | ID={detection_id[:8]}... | "
        f"Camera={camera_id} | Risk={risk_level} | Objects={n_detections}"
    )
    
    # Business rule: Tạo alert khi risk >= MEDIUM
    action_taken = "NONE"
    alert_id = None
    message = f"Kết quả đã được ghi nhận, không phát hiện vi phạm"
    
    if risk_level in ["MEDIUM", "HIGH", "CRITICAL"]:
        # Tạo alert
        alert_type = risk_to_alert_type(risk_level)
        
        # Xác định alert type cụ thể dựa vào metadata
        metadata = payload.metadata or {}
        if "unauthorized_access" in metadata.get("alert_reason", ""):
            alert_type = "UNAUTHORIZED_ACCESS"
        elif "unknown_person" in metadata.get("alert_reason", ""):
            alert_type = "UNKNOWN_PERSON"
        elif n_detections > 0 and payload.detections[0].label not in ["person"]:
            alert_type = "SUSPICIOUS_OBJECT"
        else:
            alert_type = "AI_VISION_DETECTION"
        
        alert_message = (
            f"Phát hiện {n_detections} đối tượng tại camera {camera_id} "
            f"với mức rủi ro {risk_level}"
        )
        
        alert = Alert(
            id=str(uuid.uuid4()),
            sourceService="ai-vision-gateway",
            alertType=alert_type,
            severity=risk_level,
            message=alert_message,
            relatedEventId=detection_id,
            status="OPEN",
            createdAt=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            resolvedAt=None,
        )
        
        alerts_store.append(alert)
        stats["alert_counts"][alert.status] = stats["alert_counts"].get(alert.status, 0) + 1
        
        action_taken = "ALERT_CREATED"
        alert_id = alert.id
        message = f"Phát hiện truy cập trái phép, đã tạo alert"
        
        logger.info(
            f"  🚨 Alert {alert.id[:8]}... | {alert.alertType} | "
            f"Severity={alert.severity}"
        )
    else:
        logger.info(f"  📝 LOG only | Risk={risk_level} (no alert)")
    
    # Trả acknowledgment
    ack = AIVisionResultAck(
        ack_id=str(uuid.uuid4()),
        detection_id=detection_id,
        status="ACCEPTED",
        action_taken=action_taken,
        alert_id=alert_id,
        message=message,
        processed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    
    return ack


# ═══════════════════════════════════════════════════════════════════════════
#  Startup
# ═══════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 80)
    logger.info("Core Business Mock Service starting...")
    logger.info(f"AI Vision URL: {AI_VISION_URL}")
    logger.info(f"Poll Interval: {POLL_INTERVAL}s")
    logger.info("=" * 80)
    asyncio.create_task(poll_worker())


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=6000,
        reload=False,
        log_level="info",
    )
