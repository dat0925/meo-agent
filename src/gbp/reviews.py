"""口コミ取得・返信。MOCK_MODE=true 時はダミーデータを使用。"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any

from src.db import supabase as db
from src.db.models import Review

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

_MOCK_REVIEWS = [
    {
        "gbp_review_id": "review-001",
        "reviewer_name": "田中 太郎",
        "star_rating": 5,
        "comment": "お肉が柔らかくてとても美味しかったです！スタッフの方も親切で、また来ます。",
        "created_at": datetime.utcnow() - timedelta(days=2),
    },
    {
        "gbp_review_id": "review-002",
        "reviewer_name": "佐藤 花子",
        "star_rating": 4,
        "comment": "コスパが良く満足しています。少し煙が気になりました。",
        "created_at": datetime.utcnow() - timedelta(days=5),
    },
    {
        "gbp_review_id": "review-003",
        "reviewer_name": "山田 次郎",
        "star_rating": 2,
        "comment": "注文してから30分以上待たされました。改善をお願いします。",
        "created_at": datetime.utcnow() - timedelta(hours=3),
    },
]


def fetch_and_sync_reviews(store_id: str) -> list[Review]:
    """GBPから口コミを取得してDBに同期する。"""
    reviews = []
    for r in _MOCK_REVIEWS:
        review = Review(
            store_id=store_id,
            gbp_review_id=r["gbp_review_id"],
            reviewer_name=r["reviewer_name"],
            star_rating=r["star_rating"],
            comment=r["comment"],
            reply_status="pending",
        )
        db.upsert_review(review)
        reviews.append(review)
    return reviews


def get_unanswered_reviews(store_id: str) -> list[dict[str, Any]]:
    """未返信口コミ一覧を返す。"""
    fetch_and_sync_reviews(store_id)
    pending = db.get_pending_reviews(store_id)
    return [
        {
            "review_id": r.gbp_review_id,
            "reviewer": r.reviewer_name,
            "stars": r.star_rating,
            "comment": r.comment,
            "days_ago": 0,
        }
        for r in pending
    ]


def post_reply(store_id: str, gbp_review_id: str, reply_text: str) -> dict[str, Any]:
    """口コミに返信する。"""
    if MOCK_MODE:
        success = db.mark_review_replied(gbp_review_id, reply_text)
        return {
            "success": success,
            "review_id": gbp_review_id,
            "reply": reply_text,
            "message": "返信を投稿しました（モック）",
        }
    raise NotImplementedError("本番GBP APIは未実装")
