"""GBP投稿作成・公開・履歴。MOCK_MODE=true 時はダミーデータを使用。"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

_mock_posts: list[dict[str, Any]] = [
    {
        "post_id": "post-001",
        "text": "【週末限定】黒毛和牛カルビが10%オフ！この機会をお見逃しなく🔥",
        "published_at": datetime.utcnow() - timedelta(days=35),
        "status": "published",
    },
]


def get_posts_history(store_id: str, limit: int = 10) -> dict[str, Any]:
    """過去投稿一覧と最終投稿日を返す。"""
    posts = sorted(_mock_posts, key=lambda p: p["published_at"], reverse=True)[:limit]
    last_post_at = posts[0]["published_at"] if posts else None
    days_since = (datetime.utcnow() - last_post_at).days if last_post_at else None
    return {
        "posts": [
            {
                "post_id": p["post_id"],
                "text": p["text"][:80] + "..." if len(p["text"]) > 80 else p["text"],
                "published_at": p["published_at"].strftime("%Y-%m-%d"),
                "status": p["status"],
            }
            for p in posts
        ],
        "total": len(_mock_posts),
        "last_post_at": last_post_at.strftime("%Y-%m-%d") if last_post_at else None,
        "days_since_last_post": days_since,
    }


def create_post(store_id: str, text: str, cta_type: str = "", cta_url: str = "", image_url: str = "") -> dict[str, Any]:
    """GBPに投稿を作成・公開する。"""
    if MOCK_MODE:
        new_post = {
            "post_id": f"post-{len(_mock_posts) + 1:03d}",
            "text": text,
            "published_at": datetime.utcnow(),
            "status": "published",
            "cta_type": cta_type,
            "cta_url": cta_url,
        }
        _mock_posts.append(new_post)
        return {
            "success": True,
            "post_id": new_post["post_id"],
            "message": "投稿を公開しました（モック）",
            "text_preview": text[:80],
        }
    raise NotImplementedError("本番GBP APIは未実装")
