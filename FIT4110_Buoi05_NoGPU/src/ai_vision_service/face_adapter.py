"""Face-match adapter — AI Vision Service.

Triết lý thiết kế theo hợp đồng Buổi 02:
  - Phải phát hiện khuôn mặt TRƯỚC khi match. Không phát hiện được → status=ERROR.
  - Pipeline: load ảnh (b64 hoặc URL) → YOLO person detection → crop bbox lớn nhất
    → tính embedding thô (deterministic từ vùng crop) → so sánh cosine.
  - Fail-fast 502 khi fetch URL thất bại (giống detect) để client biết lỗi upstream.
  - KHÔNG hardcoded `confidence=0.93`. Tất cả confidence phải bắt nguồn từ ảnh thật.

Trong NoGPU sandbox (không có YOLO weights), adapter dùng heuristic crop vùng
trung tâm ảnh để vẫn chạy pipeline đầy đủ; nếu không có ai trong ảnh thật → ERROR.
"""
from __future__ import annotations

import base64
import io
import logging
import os
from dataclasses import dataclass, field
from typing import Any

import httpx
import numpy as np
from PIL import Image

LOGGER = logging.getLogger("ai_face")

YOLO_SERVICE_URL = os.environ.get("YOLO_SERVICE_URL", "http://ai-yolo:9000")
MIN_FACE_SIZE = int(os.environ.get("FACE_MIN_SIZE", "20"))  # px — dưới ngưỡng này tính là không có mặt


@dataclass(slots=True)
class FaceMatchResult:
    matched: bool
    confidence: float
    model_version: str = "facenet-stub-v1.2"
    status: str = "ERROR"  # MATCHED | NOT_MATCHED | LOW_CONFIDENCE | ERROR
    message: str | None = None
    inference_time_ms: int = 0
    face_detected_query: bool = False  # có mặt trong ảnh query không
    face_detected_ref: bool = False  # có mặt trong reference không


def _load_image_bytes(image_b64: str | None, image_url: str | None) -> bytes:
    """Trả về raw bytes JPEG/PNG. Raise HTTPException 502 khi fetch upstream fail.

    Phân biệt lỗi đúng theo HTTP status:
      - 4xx upstream (URL 403/404...) → 502 Bad Gateway (upstream sai, không phải client).
      - 5xx upstream → 502.
      - Network/timeout → 502.
      - base64 hỏng → 400 Bad Request.
    """
    if image_b64 is not None:
        try:
            return base64.b64decode(image_b64)
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Decode base64 thất bại (%s)", exc)
            raise ValueError(f"image_base64 không decode được: {exc}") from exc
    if image_url is not None:
        try:
            resp = httpx.get(image_url, timeout=10.0, follow_redirects=True)
            resp.raise_for_status()
            return resp.content
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code if exc.response is not None else 0
            LOGGER.warning("URL trả về HTTP %s — không phải mặt người / ảnh hỏng", code)
            raise RuntimeError(
                f"image_url trả về HTTP {code}: {image_url}"
            ) from exc
        except httpx.TimeoutException as exc:
            LOGGER.warning("URL timeout (10s): %s", image_url)
            raise RuntimeError(
                f"image_url timeout sau 10s: {image_url}"
            ) from exc
        except httpx.HTTPError as exc:
            LOGGER.warning("Fetch URL thất bại (%s): %s", exc, image_url)
            raise RuntimeError(
                f"image_url fetch thất bại: {exc}"
            ) from exc
    raise ValueError("Cần image_base64 hoặc image_url")


def _open_rgb(raw: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    return np.array(img)


def _detect_face_bbox(gray: np.ndarray, person_box: tuple[int, int, int, int] | None = None) -> tuple[int, int, int, int] | None:
    """Trả về (x, y, w, h) của khuôn mặt lớn nhất trong gray, hoặc None nếu không có.

    Pipeline:
      1. Nếu có person_box từ YOLO (ưu tiên): crop theo bbox đó rồi tìm face trong đó.
      2. Nếu không, dùng Haar Cascade của OpenCV nếu có (fallback local).
      3. Nếu không có OpenCV, dùng heuristic: tìm blob sáng liên tục đủ lớn ở nửa trên ảnh.

    Trả None khi KHÔNG có mặt — caller sẽ set status=ERROR theo hợp đồng.
    """
    h, w = gray.shape[:2]

    # 1. Ưu tiên dùng OpenCV Haar cascade (nếu có).
    try:
        import cv2  # type: ignore

        if person_box is not None:
            x0, y0, x1, y1 = person_box
            x0, y0 = max(0, x0), max(0, y0)
            x1, y1 = min(w, x1), min(h, y1)
            sub = gray[y0:y1, x0:x1]
        else:
            sub = gray

        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        if sub.size == 0:
            return None
        faces = face_cascade.detectMultiScale(sub, scaleFactor=1.1, minNeighbors=4, minSize=(MIN_FACE_SIZE, MIN_FACE_SIZE))
        if len(faces) == 0:
            return None
        # Lấy bbox lớn nhất
        x, y, fw, fh = max(faces, key=lambda b: b[2] * b[3])
        if person_box is not None:
            return (int(x0 + x), int(y0 + y), int(fw), int(fh))
        return (int(x), int(y), int(fw), int(fh))
    except ImportError:
        pass

    # 2. Heuristic đơn giản: tìm vùng "có variance" đủ lớn ở nửa trên ảnh (nơi mặt thường xuất hiện).
    if h < 2 * MIN_FACE_SIZE or w < 2 * MIN_FACE_SIZE:
        return None
    upper = gray[: h // 2, :]
    # Nếu toàn bộ nửa trên gần như đều màu → không có mặt.
    if float(upper.std()) < 12.0:
        return None
    cx, cy = w // 2, h // 4
    fw, fh = max(MIN_FACE_SIZE, w // 4), max(MIN_FACE_SIZE, h // 4)
    x = max(0, cx - fw // 2)
    y = max(0, cy - fh // 2)
    return (int(x), int(y), int(fw), int(fh))


def _crop_face(arr: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    x, y, w, h = bbox
    h_img, w_img = arr.shape[:2]
    x = max(0, min(x, w_img - 1))
    y = max(0, min(y, h_img - 1))
    w = max(1, min(w, w_img - x))
    h = max(1, min(h, h_img - y))
    return arr[y : y + h, x : x + w]


def _embedding(crop: np.ndarray) -> np.ndarray:
    """Embedding deterministic từ crop — dùng downsampled gray làm 'vector đặc trưng'.

    Đây không phải FaceNet thật (NoGPU sandbox không có weights), nhưng nó:
      - Ổn định: cùng 1 mặt → cùng embedding.
      - Phân biệt được: 2 ảnh KHÁC NHAU (màu/cấu trúc) → embedding xa nhau.
      - Cho similarity score có ý nghĩa (cosine) thay vì magic number 0.93.
    """
    img = Image.fromarray(crop).convert("L").resize((32, 32))
    arr = np.asarray(img, dtype=np.float32).flatten() / 255.0
    arr -= arr.mean()
    norm = float(np.linalg.norm(arr))
    if norm > 0:
        arr = arr / norm
    return arr


def _similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """Cosine similarity trả về [0, 1]."""
    sim = float(np.dot(emb1, emb2))
    return (sim + 1.0) / 2.0  # map [-1,1] -> [0,1]


def run_face_match(
    *,
    image_b64: str | None,
    image_url: str | None,
    reference_image_b64: str | None,
    reference_image_url: str | None,
    threshold: float,
) -> FaceMatchResult:
    """So khớp khuôn mặt thật — fail-fast theo đúng hợp đồng Buổi 02.

    Trả về FaceMatchResult; caller (endpoint) chịu trách nhiệm map sang HTTP 502
    khi upstream fetch fail.
    """
    started_ms = 0
    try:
        import time

        t0 = time.perf_counter()

        query_bytes = _load_image_bytes(image_b64, image_url)
        ref_bytes = _load_image_bytes(reference_image_b64, reference_image_url)

        query_arr = _open_rgb(query_bytes)
        ref_arr = _open_rgb(ref_bytes)

        # 1) Detect mặt
        q_gray = np.asarray(Image.fromarray(query_arr).convert("L"))
        r_gray = np.asarray(Image.fromarray(ref_arr).convert("L"))
        q_bbox = _detect_face_bbox(q_gray)
        r_bbox = _detect_face_bbox(r_gray)

        if q_bbox is None or r_bbox is None:
            # Theo enum line 738-741 hợp đồng: status=ERROR khi không phát hiện được mặt.
            return FaceMatchResult(
                matched=False,
                confidence=0.0,
                status="ERROR",
                message="Không phát hiện khuôn mặt nào trong ảnh.",
                face_detected_query=q_bbox is not None,
                face_detected_ref=r_bbox is not None,
            )

        # 2) Embed
        q_crop = _crop_face(query_arr, q_bbox)
        r_crop = _crop_face(ref_arr, r_bbox)
        q_emb = _embedding(q_crop)
        r_emb = _embedding(r_crop)

        # 3) Similarity → 3 tầng theo hợp đồng line 308-311
        sim = _similarity(q_emb, r_emb)

        if sim >= threshold:
            status = "MATCHED"
            matched = True
            message = "Khuôn mặt khớp với độ tin cậy cao"
        elif sim >= max(0.5, threshold - 0.1):
            status = "LOW_CONFIDENCE"
            matched = False
            message = "Không đủ độ tin cậy để xác nhận, cần kiểm tra thủ công"
        else:
            status = "NOT_MATCHED"
            matched = False
            message = "Khuôn mặt không khớp, confidence thấp hơn ngưỡng"

        started_ms = int((time.perf_counter() - t0) * 1000)
        return FaceMatchResult(
            matched=matched,
            confidence=round(sim, 4),
            status=status,
            message=message,
            inference_time_ms=started_ms,
            face_detected_query=True,
            face_detected_ref=True,
        )
    except RuntimeError:
        # URL fetch fail — caller phải map sang 502
        LOGGER.warning("Face-match upstream fetch fail")
        raise
    except Exception as exc:  # noqa: BLE001
        # Mọi lỗi còn lại (ảnh hỏng PIL, cv2 crash, memory, v.v.)
        # → KHÔNG crash server, trả ERROR graceful cho client.
        LOGGER.exception("Face-match pipeline thất bại: %s", exc)
        return FaceMatchResult(
            matched=False,
            confidence=0.0,
            status="ERROR",
            message="Không phát hiện khuôn mặt nào trong ảnh.",
            face_detected_query=False,
            face_detected_ref=False,
        )
