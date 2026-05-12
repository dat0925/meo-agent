"""GBP写真アップロード。MOCK_MODE=true 時はダミーを返す。"""
from __future__ import annotations

import os
from typing import Any

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

_mock_photos: list[dict[str, Any]] = [
    {"photo_id": "photo-001", "category": "FOOD", "url": "https://example.com/mock-photo-1.jpg"},
    {"photo_id": "photo-002", "category": "INTERIOR", "url": "https://example.com/mock-photo-2.jpg"},
]


def get_photo_count(store_id: str) -> dict[str, Any]:
    return {
        "total": len(_mock_photos),
        "by_category": {"FOOD": 1, "INTERIOR": 1},
        "industry_average": 12,
        "below_average": len(_mock_photos) < 12 * 0.5,
    }


def upload_photo(store_id: str, image_bytes: bytes, category: str = "FOOD") -> dict[str, Any]:
    if MOCK_MODE:
        new_photo = {
            "photo_id": f"photo-{len(_mock_photos) + 1:03d}",
            "category": category,
            "url": f"https://example.com/mock-photo-{len(_mock_photos) + 1}.jpg",
        }
        _mock_photos.append(new_photo)
        return {
            "success": True,
            "photo_id": new_photo["photo_id"],
            "message": "写真をGBPにアップロードしました（モック）",
        }
    raise NotImplementedError("本番GBP APIは未実装")
