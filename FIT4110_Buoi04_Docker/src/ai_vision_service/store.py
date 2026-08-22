"""In-memory store cho detection results (đơn giản, chỉ phục vụ local test)."""
from __future__ import annotations

import base64
from collections import deque
from typing import Any

from .schemas import DetectResponse


class DetectionStore:
    """Lưu trữ tạm các detection trong bộ nhớ, có giới hạn 1000 record gần nhất."""

    def __init__(self, max_records: int = 1000) -> None:
        self._records: dict[str, DetectResponse] = {}
        self._order: deque[str] = deque(maxlen=max_records)

    def add(self, response: DetectResponse) -> None:
        self._records[response.detection_id] = response
        self._order.append(response.detection_id)

    def get(self, detection_id: str) -> DetectResponse | None:
        return self._records.get(detection_id)

    def list_recent(
        self,
        limit: int,
        camera_id: str | None = None,
    ) -> tuple[list[DetectResponse], str | None, bool]:
        items: list[DetectResponse] = []
        for did in reversed(self._order):
            record = self._records[did]
            if camera_id and record.camera_id != camera_id:
                continue
            items.append(record)
            if len(items) >= limit:
                break

        has_more = len(items) == limit and len(self._order) > limit
        next_cursor = base64.b64encode(items[-1].timestamp.encode()).decode() if items and has_more else None
        return items, next_cursor, has_more
