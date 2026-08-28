"""
Trang So sánh khuôn mặt
So sánh hai khuôn mặt để kiểm tra giống nhau
"""
import streamlit as st
import requests
import time
from PIL import Image
import io
import base64
import httpx
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("AI_VISION_API_URL", "http://localhost:8000")
AUTH_TOKEN = os.getenv("AI_VISION_AUTH_TOKEN", "local-dev-token-vision")


def get_headers():
    return {"Authorization": f"Bearer {AUTH_TOKEN}"}


def fetch_image_from_url(url: str) -> Image.Image | None:
    try:
        response = httpx.get(url, timeout=15, follow_redirects=True)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content))
    except Exception:
        return None


def img_to_base64(image: Image.Image) -> str:
    buf = io.BytesIO()
    fmt = image.format or "JPEG"
    image.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


st.title("So sánh khuôn mặt")
st.markdown("So sánh hai khuôn mặt để kiểm tra độ giống nhau")
st.markdown("---")

st.subheader("Tải hai ảnh để so sánh")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Ảnh 1")
    img1_url = st.text_input("Link ảnh 1", placeholder="https://...", key="img1_url")
    img1_file = st.file_uploader(
        "hoặc tải ảnh lên",
        type=['jpg', 'jpeg', 'png'],
        key="file1"
    )

    image1 = None
    if img1_file:
        image1 = Image.open(img1_file)
        st.image(image1, caption="Ảnh 1", use_container_width=True)
    elif img1_url:
        with st.spinner("Đang tải ảnh..."):
            image1 = fetch_image_from_url(img1_url)
            if image1:
                st.image(image1, caption="Ảnh 1", use_container_width=True)
            else:
                st.error("Không thể tải ảnh từ URL")

with col2:
    st.markdown("#### Ảnh 2")
    img2_url = st.text_input("Link ảnh 2", placeholder="https://...", key="img2_url")
    img2_file = st.file_uploader(
        "hoặc tải ảnh lên",
        type=['jpg', 'jpeg', 'png'],
        key="file2"
    )

    image2 = None
    if img2_file:
        image2 = Image.open(img2_file)
        st.image(image2, caption="Ảnh 2", use_container_width=True)
    elif img2_url:
        with st.spinner("Đang tải ảnh..."):
            image2 = fetch_image_from_url(img2_url)
            if image2:
                st.image(image2, caption="Ảnh 2", use_container_width=True)
            else:
                st.error("Không thể tải ảnh từ URL")


if st.button("So sánh khuôn mặt", type="primary", disabled=not (image1 and image2)):
    if not image1:
        st.error("Vui lòng nhập ảnh 1")
    elif not image2:
        st.error("Vui lòng nhập ảnh 2")
    else:
        with st.spinner("Đang so sánh..."):
            start_time = time.time()

            ref_b64 = img_to_base64(image1)
            test_b64 = img_to_base64(image2)

            payload = {
                "reference_image_base64": ref_b64,
                "image_base64": test_b64,
                "threshold": 0.7,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

            try:
                response = requests.post(
                    f"{API_URL}/vision/face-match",
                    headers={**get_headers(), "Content-Type": "application/json"},
                    json=payload,
                    timeout=60
                )

                elapsed = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    result = response.json()
                    st.success(f"So sánh hoàn tất trong {elapsed:.0f}ms")

                    st.subheader("Kết quả so sánh")

                    matched = result.get('matched', False)
                    confidence = result.get('confidence', 0)

                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("ID So sánh", result.get('match_id', 'N/A'))
                    with col_b:
                        st.metric("Độ tự tin", f"{confidence:.2%}")
                    with col_c:
                        status = "GIỐNG NHAU" if matched else "KHÁC NHAU"
                        st.metric("Kết quả", status)

                    st.progress(confidence, text=f"Độ giống nhau: {confidence:.1%}")

                    if matched:
                        st.success("Hai khuôn mặt có thể là cùng một người")
                    else:
                        st.warning("Hai khuôn mặt có thể là hai người khác nhau")

                    message = result.get('message')
                    if message:
                        st.info(f"Ghi chú: {message}")

                    with st.expander("Dữ liệu phản hồi thuần"):
                        st.json(result)

                else:
                    st.error(f"Lỗi: {response.status_code}")
                    try:
                        st.json(response.json())
                    except Exception:
                        st.text(response.text)

            except requests.exceptions.Timeout:
                st.error("Yêu cầu hết thời gian. Vui lòng thử lại.")
            except Exception as e:
                st.error(f"Lỗi: {str(e)}")


st.markdown("---")
st.caption("Lưu ý: Sử dụng ảnh khuôn mặt rõ ràng, thẳng mặt để đạt kết quả tốt nhất")
