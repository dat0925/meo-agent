"""
インメモリDBモック。
MOCK_MODE=true のときはこのモジュールがSupabaseの代わりに動作する。
本番切り替え時はこのファイルを supabase-py クライアントに差し替える。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from src.db.models import Conversation, Review, Store


# ---- インメモリストレージ ----

_stores: dict[str, Store] = {}          # key: line_user_id
_conversations: list[Conversation] = []
_reviews: dict[str, Review] = {}        # key: gbp_review_id

# デモ用の初期店舗データ
_DEFAULT_STORE = Store(
    id="store-demo-001",
    line_user_id="mock_user_001",
    gbp_location_id="locations/mock-location-001",
    store_name="焼肉 大将",
    store_category="焼肉店",
)
_stores[_DEFAULT_STORE.line_user_id] = _DEFAULT_STORE


# ---- Store CRUD ----

def get_store_by_line_user(line_user_id: str) -> Store | None:
    return _stores.get(line_user_id)


def upsert_store(store: Store) -> Store:
    _stores[store.line_user_id] = store
    return store


def get_all_stores() -> list[Store]:
    return list(_stores.values())


# ---- Conversation CRUD ----

def save_message(store_id: str, role: str, content: str, metadata: dict[str, Any] | None = None) -> Conversation:
    conv = Conversation(
        store_id=store_id,
        channel="line",
        role=role,
        content=content,
        metadata=metadata or {},
    )
    _conversations.append(conv)
    return conv


def get_recent_conversations(store_id: str, limit: int = 20) -> list[Conversation]:
    store_convs = [c for c in _conversations if c.store_id == store_id]
    return store_convs[-limit:]


# ---- Review CRUD ----

def upsert_review(review: Review) -> Review:
    _reviews[review.gbp_review_id] = review
    return review


def get_pending_reviews(store_id: str) -> list[Review]:
    return [r for r in _reviews.values() if r.store_id == store_id and r.reply_status == "pending"]


def mark_review_replied(gbp_review_id: str, reply_text: str) -> bool:
    if gbp_review_id not in _reviews:
        return False
    _reviews[gbp_review_id].reply_text = reply_text
    _reviews[gbp_review_id].reply_status = "replied"
    _reviews[gbp_review_id].replied_at = datetime.utcnow()
    return True
