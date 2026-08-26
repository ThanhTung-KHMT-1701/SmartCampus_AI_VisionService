# Smart Campus — Service Mock

Mock services để kiểm thử tích hợp với AI Vision Service.

## 📦 Services

### 1. Camera Stream Mock (Port 5000)
**Vai trò**: Upstream service - gửi frames đến AI Vision

**Features**:
- Tự động gửi frames mỗi 10 giây
- Sử dụng test images từ Picsum
- Lưu lịch sử frames đã gửi
- Expose API để xem stats và history

**Endpoints**:
- `GET /health` - Health check
- `GET /status` - Trạng thái stream
- `GET /frames/history` - Lịch sử frames đã gửi
- `GET /stats` - Thống kê
- `POST /stream/start` - Bắt đầu stream
- `POST /stream/stop` - Dừng stream
- `POST /frames/send` - Gửi 1 frame thủ công

### 2. Core Business Mock (Port 6000)
**Vai trò**: Downstream service - nhận kết quả từ AI Vision

**Features**:
- Tự động poll AI Vision mỗi 15 giây
- Xử lý business logic dựa trên risk_level
- Quyết định action: LOG, ALERT, ESCALATE
- Expose dashboard và metrics

**Endpoints**:
- `GET /health` - Health check
- `GET /detections` - Danh sách detections đã xử lý
- `GET /detections/{id}` - Chi tiết detection
- `GET /metrics` - Business metrics
- `GET /dashboard` - Dashboard tổng quan
- `POST /poll/start` - Bắt đầu polling
- `POST /poll/stop` - Dừng polling
- `POST /poll/now` - Poll ngay lập tức

## 🚀 Quick Start

### Prerequisites
```bash
# Đảm bảo AI Vision Service đang chạy
cd FIT4110_Buoi05_GPU
docker-compose ps

# AI Vision Gateway phải healthy trên port 8000
```

### Build & Run
```bash
cd ServiceMock

# Build images
docker-compose build --no-cache

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## 🔄 Integration Flow

```
Camera Stream (5000)  →  AI Vision Gateway (8000)  →  Core Business (6000)
        │                        │                            │
        │ POST /vision/detect    │                            │
        ├───────────────────────>│                            │
        │                        │ Process with AI             │
        │                        │ Save to MySQL              │
        │<───────────────────────┤                            │
        │   Detection result     │                            │
        │                        │                            │
        │                        │ GET /vision/results/recent │
        │                        │<───────────────────────────┤
        │                        │                            │
        │                        │ Recent detections          │
        │                        ├───────────────────────────>│
        │                        │                            │
        │                        │                      Business Logic
        │                        │                      (LOG/ALERT/ESCALATE)
```

## 🧪 Testing

### 1. Check Services Health
```bash
# Camera Stream
curl http://localhost:5000/health

# Core Business
curl http://localhost:6000/health
```

### 2. Monitor Camera Stream
```bash
# View stream status
curl http://localhost:5000/status

# View frame history
curl http://localhost:5000/frames/history

# View statistics
curl http://localhost:5000/stats
```

### 3. Monitor Core Business
```bash
# View dashboard
curl http://localhost:6000/dashboard

# View metrics
curl http://localhost:6000/metrics

# View processed detections
curl http://localhost:6000/detections?limit=10

# Filter by risk level
curl http://localhost:6000/detections?risk_level=HIGH
```

### 4. Manual Operations
```bash
# Camera Stream: Send 1 frame manually
curl -X POST http://localhost:5000/frames/send

# Core Business: Trigger poll immediately
curl -X POST http://localhost:6000/poll/now
```

## 📊 Expected Behavior

### Camera Stream
- Gửi frame mỗi **10 giây**
- Mỗi frame nhận response từ AI Vision (~700-800ms)
- Success rate ~100% nếu AI Vision healthy

### Core Business
- Poll AI Vision mỗi **15 giây**
- Nhận 10 recent detections mỗi lần poll
- Xử lý business logic:
  - **CRITICAL** risk → ESCALATE action
  - **HIGH** risk → ALERT action
  - **MEDIUM** risk + nhiều objects → ALERT action
  - **LOW** risk → LOG action

## 🐛 Troubleshooting

### Issue: Camera Stream không gửi được frames
```bash
# Check AI Vision Gateway healthy
curl http://localhost:8000/health

# Check network connectivity
docker network inspect class-net

# Check auth token
grep AI_VISION_TOKEN .env
```

### Issue: Core Business không nhận được detections
```bash
# Check AI Vision có data
curl -H "Authorization: Bearer smartcampus-vision-2026-secure-token" \
  http://localhost:8000/vision/results/recent

# Check Core Business logs
docker logs smartcampus-core-business-mock -f
```

### Issue: Services unhealthy
```bash
# Rebuild services
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Wait 20s for health checks
sleep 20
docker-compose ps
```

## 📁 Project Structure

```
ServiceMock/
├── docker-compose.yml
├── .env
├── README.md
│
├── camera-stream/
│   ├── app.py              # FastAPI application
│   ├── Dockerfile
│   └── requirements.txt
│
└── core-business/
    ├── app.py              # FastAPI application
    ├── Dockerfile
    └── requirements.txt
```

## 🌐 Networks

```yaml
class-net:
  - ai-vision-gateway (8000)    # From FIT4110_Buoi05_GPU
  - camera-stream-mock (5000)
  - core-business-mock (6000)
```

## 🔐 Security

- Sử dụng Bearer Token authentication
- Token được cấu hình trong `.env`
- Phải match với token trong AI Vision Gateway

## 📈 Monitoring

### Real-time Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f camera-stream-mock
docker-compose logs -f core-business-mock
```

### Metrics Dashboard
```bash
# Camera Stream stats
curl http://localhost:5000/stats | jq

# Core Business metrics
curl http://localhost:6000/metrics | jq

# Core Business dashboard
curl http://localhost:6000/dashboard | jq
```

## 🎯 Success Criteria

✅ Camera Stream gửi frames liên tục  
✅ AI Vision xử lý và trả về detections  
✅ Core Business poll và xử lý kết quả  
✅ All services healthy  
✅ Success rate > 95%

## 🛑 Stop Services

```bash
cd ServiceMock
docker-compose down

# Remove volumes (if needed)
docker-compose down -v
```

---

**Last Updated**: 2026-08-27  
**Version**: 1.0.0
