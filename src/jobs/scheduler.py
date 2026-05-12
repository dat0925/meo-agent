"""
監視ジョブ。Cloud Scheduler から HTTP POSTで呼び出される想定。
MOCK_MODE時も同一ロジックが動き、LINE通知はコンソール出力になる。
"""
from __future__ import annotations

from datetime import datetime, timedelta

from src.db import supabase as db
from src.gbp import posts as gbp_posts
from src.gbp import reviews as gbp_reviews
from src.jobs.notifier import push_message


async def run_review_check() -> dict:
    """未返信口コミを検知してLINE通知。毎時実行想定。"""
    results = []
    for store in db.get_all_stores():
        if not store.notification_enabled:
            continue
        pending = gbp_reviews.get_unanswered_reviews(store.id)
        if not pending:
            continue

        complaints = [r for r in pending if r["stars"] <= 2]
        normal = [r for r in pending if r["stars"] >= 3]

        if complaints:
            text = f"⚠️ 苦情口コミが{len(complaints)}件届いています（★{complaints[0]['stars']}）。\n返信文を用意しましょうか？"
            await push_message(store.line_user_id, text)
        elif normal:
            text = f"💬 新しい口コミが{len(normal)}件届いています（★{normal[0]['stars']}）。\n返信しますか？"
            await push_message(store.line_user_id, text)

        results.append({"store_id": store.id, "pending_count": len(pending)})
    return {"job": "review_check", "processed": results}


async def run_post_reminder() -> dict:
    """投稿不足を検知してLINE通知。毎日9:00想定。"""
    results = []
    for store in db.get_all_stores():
        if not store.notification_enabled:
            continue
        history = gbp_posts.get_posts_history(store.id)
        days_since = history.get("days_since_last_post")
        if days_since is not None and days_since >= 7:
            text = f"📝 投稿が{days_since}日ありません。\nGBPの露出を高めるために投稿案を作りましょうか？"
            await push_message(store.line_user_id, text)
            results.append({"store_id": store.id, "days_since": days_since})
    return {"job": "post_reminder", "processed": results}


async def run_photo_audit() -> dict:
    """写真不足を検知してLINE通知。毎週月曜想定。"""
    from src.gbp import photos as gbp_photos

    results = []
    for store in db.get_all_stores():
        if not store.notification_enabled:
            continue
        info = gbp_photos.get_photo_count(store.id)
        if info.get("below_average"):
            text = f"📸 写真が{info['total']}枚と少なめです（業種平均: {info['industry_average']}枚）。\n写真を追加しませんか？"
            await push_message(store.line_user_id, text)
            results.append({"store_id": store.id, "photo_count": info["total"]})
    return {"job": "photo_audit", "processed": results}
