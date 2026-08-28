"""
SmartCampus AI Vision - Dashboard
Tổng quan hệ thống và trang chính
"""
import streamlit as st
import requests
import time
from datetime import datetime
import os
from dotenv import load_dotenv
import torch

load_dotenv()

API_URL = os.getenv("AI_VISION_API_URL", "http://localhost:8000")
AUTH_TOKEN = os.getenv("AI_VISION_AUTH_TOKEN", "local-dev-token-vision")

st.set_page_config(
    page_title="SmartCampus AI Vision",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    :root {
        --primary-color: #1976D2;
        --success-color: #388E3C;
        --error-color: #D32F2F;
        --warning-color: #F57C00;
        --bg-color: #FAFAFA;
    }
    [data-testid="stSidebar"] { background-color: #E3F2FD; }
    h1 { color: #1565C0; font-weight: 600; }
    h2 { color: #1976D2; font-weight: 500; }
    .stButton > button {
        background-color: #1976D2;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
    }
    .stButton > button:hover { background-color: #1565C0; }
    [data-testid="stMetricValue"] { color: #1976D2; }
</style>
""", unsafe_allow_html=True)


def get_headers():
    return {"Authorization": f"Bearer {AUTH_TOKEN}"}


def check_api_health():
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        return False, None
    except Exception as e:
        return False, str(e)


def get_model_info():
    try:
        response = requests.get(
            f"{API_URL}/vision/models/info",
            headers=get_headers(),
            timeout=5
        )
        if response.status_code == 200:
            return True, response.json()
        return False, response.json() if response.content else None
    except Exception as e:
        return False, str(e)


# Sidebar
st.sidebar.title("SmartCampus AI Vision")
st.sidebar.markdown("---")

device = "cuda" if torch.cuda.is_available() else "cpu"
st.sidebar.success(f"Device: {device.upper()}")

with st.sidebar:
    is_healthy, data = check_api_health()
    if is_healthy:
        st.success("API Đang hoạt động")
        with st.expander("Chi tiết"):
            st.json(data)
    else:
        st.error("API Không hoạt động")
        st.caption(f"Lỗi: {data}")

st.sidebar.markdown("---")
st.sidebar.caption(f"Địa chỉ API: {API_URL}")


# Main content
st.title("Dashboard")
st.markdown("Tổng quan và thống kê hệ thống")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Kiểm tra trạng thái hệ thống")
    is_healthy, data = check_api_health()

    if is_healthy:
        st.success("Tất cả hệ thống đang hoạt động")

        metrics = {
            "Trạng thái": data.get("status", "N/A"),
            "Dịch vụ": data.get("service", "N/A"),
            "Phiên bản": data.get("version", "N/A"),
            "Model đã tải": "Có" if data.get("modelLoaded") else "Không",
            "Thời gian": data.get("time", "N/A")
        }

        for key, value in metrics.items():
            st.metric(key, value)
    else:
        st.error("Dịch vụ không sẵn sàng")
        st.caption(f"Lỗi: {data}")

with col2:
    st.subheader("Thông tin model")
    success, model_data = get_model_info()

    if success:
        st.info(f"**ID Model:** {model_data.get('model_id', 'N/A')}")

        model_metrics = {
            "Loại model": model_data.get("model_type", "N/A"),
            "Framework": model_data.get("framework", "N/A"),
            "Phiên bản Framework": model_data.get("framework_version", "N/A"),
        }

        for key, value in model_metrics.items():
            st.metric(key, value)

        classes = model_data.get("classes", [])
        if classes:
            st.markdown("**Danh sách lớp phát hiện:**")
            names = [c.get("name", "") for c in classes]
            st.write(", ".join(names))

        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.metric("Ngưỡng mặc định", f"{model_data.get('confidence_threshold_default', 'N/A')}")
        with col_info2:
            st.metric("Kích thước đầu vào", model_data.get('input_size', 'N/A'))
        col_info3, col_info4 = st.columns(2)
        with col_info3:
            st.metric("Độ chính xác mAP", f"{model_data.get('accuracy_map', 'N/A')}")
        with col_info4:
            st.metric("Thời gian suy luận TB", f"{model_data.get('inference_time_ms_avg', 'N/A')}ms")
    else:
        st.warning("Không thể lấy thông tin model")

st.markdown("---")

st.subheader("Kiểm tra nhanh API")

test_col1, test_col2 = st.columns(2)

with test_col1:
    if st.button("Kiểm tra endpoint /health"):
        with st.spinner("Đang kiểm tra..."):
            start = time.time()
            try:
                response = requests.get(f"{API_URL}/health", timeout=10)
                elapsed = (time.time() - start) * 1000
                st.json(response.json())
                st.success(f"Thời gian phản hồi: {elapsed:.0f}ms")
            except Exception as e:
                st.error(f"Lỗi: {e}")

with test_col2:
    if st.button("Kiểm tra endpoint /vision/models/info"):
        with st.spinner("Đang kiểm tra..."):
            start = time.time()
            try:
                response = requests.get(
                    f"{API_URL}/vision/models/info",
                    headers=get_headers(),
                    timeout=10
                )
                elapsed = (time.time() - start) * 1000
                st.json(response.json())
                st.success(f"Thời gian phản hồi: {elapsed:.0f}ms")
            except Exception as e:
                st.error(f"Lỗi: {e}")

st.markdown("---")

st.subheader("Các lần phát hiện gần đây")

try:
    response = requests.get(
        f"{API_URL}/vision/results/recent",
        headers=get_headers(),
        params={"limit": 5},
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])

        if items:
            for item in items:
                with st.container():
                    col_a, col_b, col_c = st.columns([2, 1, 1])
                    with col_a:
                        st.markdown(f"**Camera:** `{item.get('camera_id', 'N/A')}`")
                        st.caption(f"ID: {item.get('detection_id', 'N/A')}")
                    with col_b:
                        objects = item.get('detections', [])
                        st.metric("Số đối tượng", len(objects))
                    with col_c:
                        st.caption(item.get('timestamp', 'N/A')[:19])
                    st.markdown("---")
        else:
            st.info("Không có lần phát hiện nào gần đây")
    else:
        st.warning(f"Không thể lấy dữ liệu phát hiện (Mã: {response.status_code})")
except Exception as e:
    st.error(f"Lỗi: {e}")

st.markdown("---")
st.caption(f"Cập nhật lần cuối: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
