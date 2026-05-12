"""
GBP APIクライアント。
MOCK_MODE=true の場合はすべてダミーデータを返す。
本番時は Google Business Profile API v4.9 を呼び出す。
"""
from __future__ import annotations

import os
from typing import Any


MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"


class GBPClient:
    def __init__(self, access_token: str = "", location_id: str = ""):
        self.access_token = access_token
        self.location_id = location_id or "locations/mock-location-001"

    def get_stats(self) -> dict[str, Any]:
        if MOCK_MODE:
            return {
                "location_id": self.location_id,
                "period": "直近30日",
                "search_impressions": 1240,
                "map_impressions": 830,
                "website_clicks": 95,
                "direction_requests": 42,
                "phone_calls": 18,
                "photo_views": 3200,
            }
        raise NotImplementedError("本番GBP APIは未実装")

    def get_location_info(self) -> dict[str, Any]:
        if MOCK_MODE:
            return {
                "name": self.location_id,
                "store_name": "焼肉 大将",
                "category": "焼肉店",
                "address": "東京都渋谷区〇〇1-2-3",
                "phone": "03-1234-5678",
            }
        raise NotImplementedError("本番GBP APIは未実装")
