"""
Trang Phát hiện đối tượng
Upload ảnh hoặc nhập URL để phát hiện đối tượng
Sử dụng YOLO trực tiếp trên máy (CPU/GPU tự động phát hiện)
"""
import streamlit as st
import time
from PIL import Image
import io
import sys
from datetime import datetime
import base64
import uuid
import numpy as np
import torch

# Lazy import YOLO - chỉ load khi cần
_yolo_model = None

def get_yolo_model():
    """Load YOLO model, tự động dùng GPU nếu có, CPU nếu không"""
    global _yolo_model
    if _yolo_model is None:
        from ultralytics import YOLO
        device = "cuda" if torch.cuda.is_available() else "cpu"
        st.info(f"Loading YOLO model trên {device.upper()}...")
        _yolo_model = YOLO("yolov8n.pt")
        _yolo_model.to(device)
    return _yolo_model

def img_to_base64(image: Image.Image) -> str:
    buf = io.BytesIO()
    fmt = image.format or "JPEG"
    image.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def detect_objects(image: Image.Image, camera_id: str):
    """Phát hiện đối tượng trong ảnh sử dụng YOLO trực tiếp"""
    global _yolo_model
    
    t0 = time.perf_counter()
    model = get_yolo_model()
    
    # Chuyển PIL Image sang numpy array RGB
    img_rgb = np.array(image.convert("RGB"))
    
    # Run YOLO detection
    results = model(img_rgb, conf=0.25, iou=0.45, max_det=50, verbose=False)
    result = results[0] if isinstance(results, list) else results
    
    processing_time_ms = int((time.perf_counter() - t0) * 1000)
    detection_id = str(uuid.uuid4())
    
    # Parse kết quả
    detections = []
    boxes = result.boxes
    if boxes is not None and len(boxes) > 0:
        cls_ids = boxes.cls.cpu().numpy().astype(int)
        confs = boxes.conf.cpu().numpy()
        xyxy = boxes.xyxy.cpu().numpy()
        
        for cls_id, conf, (x1, y1, x2, y2) in zip(cls_ids, confs, xyxy):
            label = result.names[int(cls_id)]
            detections.append({
                "label": label,
                "confidence": float(conf),
                "bbox": {
                    "x": int(x1),
                    "y": int(y1),
                    "width": int(x2 - x1),
                    "height": int(y2 - y1)
                },
                "class_id": int(cls_id)
            })
    
    # Tính risk level
    high_risk = {"person", "car", "truck", "bus", "motorcycle"}
    medium_risk = {"backpack", "handbag", "suitcase"}
    
    risk = "LOW"
    labels = [d["label"] for d in detections]
    confs = [d["confidence"] for d in detections]
    
    for label, conf in zip(labels, confs):
        if label in high_risk and conf >= 0.85:
            risk = "HIGH"
            break
        elif label in medium_risk:
            risk = "MEDIUM"
    
    return {
        "detection_id": detection_id,
        "camera_id": camera_id,
        "detections": detections,
        "risk_level": risk,
        "model_version": "yolov8n",
        "processing_time_ms": processing_time_ms,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

st.title("Phát hiện đối tượng")
st.markdown("Nhận diện các đối tượng trong ảnh bằng YOLO")

st.markdown("""
<style>
    .detection-results .stMetric label {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
    }
    .detection-results .stMetric [data-testid="stMetricValue"] {
        font-size: 0.7rem !important;
        word-break: break-all !important;
        white-space: normal !important;
        line-height: 1.3 !important;
    }
    .detection-results .stMetric [data-testid="stMetricValue"] p {
        font-size: 0.7rem !important;
        margin: 0 !important;
    }
    .detection-results .stMetricValue {
        font-size: 0.7rem !important;
    }
    .detection-results .stExpander {
        font-size: 0.8rem !important;
    }
    .detection-results details > summary {
        font-size: 0.85rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Hiển thị device info
device = "cuda" if torch.cuda.is_available() else "cpu"
st.caption(f"Device: {device.upper()}")

st.markdown("---")

input_method = st.radio(
    "Chọn phương thức nhập:",
    ["Tải lên ảnh", "Sử dụng link ảnh"],
    horizontal=True
)

camera_id = st.text_input("ID Camera", value="cam-demo-01", help="Mã số nhận dạng camera")

def make_timestamp():
    return datetime.utcnow().isoformat() + "Z"


# ---- Tải lên ảnh ----
if input_method == "Tải lên ảnh":
    st.subheader("Tải ảnh lên")
    uploaded_file = st.file_uploader(
        "Chọn tệp tin ảnh",
        type=['jpg', 'jpeg', 'png', 'bmp'],
        help="Định dạng hỗ trợ: JPG, PNG, BMP"
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Ảnh đã tải lên", use_container_width=True)

        if st.button("Phát hiện đối tượng", type="primary"):
            with st.spinner("Đang phân tích ảnh..."):
                start_time = time.time()
                image = Image.open(uploaded_file)

                try:
                    result = detect_objects(image, camera_id)
                    elapsed = (time.time() - start_time) * 1000

                    st.success(f"Phân tích hoàn tất trong {elapsed:.0f}ms")

                    st.markdown('<div class="detection-results">', unsafe_allow_html=True)
                    st.subheader("Kết quả phát hiện")

                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("ID Phát hiện", result.get('detection_id', 'N/A'))
                    with col_b:
                        st.metric("Số đối tượng", len(result.get('detections', [])))
                    with col_c:
                        proc_time = result.get('processing_time_ms', 0)
                        st.metric("Thời gian xử lý", f"{proc_time:.0f}ms")

                    risk = result.get('risk_level', 'LOW')
                    if risk == 'HIGH':
                        st.error(f"Mức cảnh báo: {risk}")
                    elif risk == 'MEDIUM':
                        st.warning(f"Mức cảnh báo: {risk}")
                    else:
                        st.info(f"Mức cảnh báo: {risk}")

                    detections = result.get('detections', [])
                    if detections:
                        st.markdown("### Đối tượng phát hiện được")
                        for i, det in enumerate(detections):
                            with st.expander(f"Đối tượng {i+1}: {det.get('label', 'Không rõ')} ({det.get('confidence', 0)*100:.1f}%)"):
                                st.json(det)
                    else:
                        st.info("Không phát hiện đối tượng nào trong ảnh này")

                    with st.expander("Dữ liệu phản hồi thuần"):
                        st.json(result)

                except Exception as e:
                    st.error(f"Lỗi: {str(e)}")
                    st.markdown('</div>', unsafe_allow_html=True)


# ---- Link ảnh ----
else:
    import requests as req
    
    st.subheader("Nhập link ảnh")
    image_url = st.text_input(
        "Link ảnh",
        placeholder="https://example.com/image.jpg",
        help="Nhập liên kết trực tiếp đến ảnh"
    )

    if image_url:
        try:
            st.image(image_url, caption="Ảnh nguồn", use_container_width=True)
        except Exception:
            st.warning("Không thể tải ảnh từ link")

        if st.button("Phát hiện đối tượng", type="primary"):
            with st.spinner("Đang phân tích ảnh..."):
                start_time = time.time()

                try:
                    response = req.get(image_url, timeout=30)
                    response.raise_for_status()
                    image = Image.open(io.BytesIO(response.content))

                    result = detect_objects(image, camera_id)
                    elapsed = (time.time() - start_time) * 1000

                    st.success(f"Phân tích hoàn tất trong {elapsed:.0f}ms")

                    st.markdown('<div class="detection-results">', unsafe_allow_html=True)
                    st.subheader("Kết quả phát hiện")

                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("ID Phát hiện", result.get('detection_id', 'N/A'))
                    with col_b:
                        st.metric("Số đối tượng", len(result.get('detections', [])))
                    with col_c:
                        proc_time = result.get('processing_time_ms', 0)
                        st.metric("Thời gian xử lý", f"{proc_time:.0f}ms")

                    risk = result.get('risk_level', 'LOW')
                    if risk == 'HIGH':
                        st.error(f"Mức cảnh báo: {risk}")
                    elif risk == 'MEDIUM':
                        st.warning(f"Mức cảnh báo: {risk}")
                    else:
                        st.info(f"Mức cảnh báo: {risk}")

                    detections = result.get('detections', [])
                    if detections:
                        st.markdown("### Đối tượng phát hiện được")
                        for i, det in enumerate(detections):
                            with st.expander(f"Đối tượng {i+1}: {det.get('label', 'Không rõ')} ({det.get('confidence', 0)*100:.1f}%)"):
                                st.json(det)
                    else:
                        st.info("Không phát hiện đối tượng nào trong ảnh này")

                    with st.expander("Dữ liệu phản hồi thuần"):
                        st.json(result)

                except Exception as e:
                    st.error(f"Lỗi: {str(e)}")

                st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("Lưu ý: Sử dụng ảnh rõ ràng để đạt kết quả tốt nhất")
