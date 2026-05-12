"""会話履歴管理。DBから復元してClaude APIのmessages形式に変換する。"""
from __future__ import annotations

from typing import Any

from src.db import supabase as db


def load_history(store_id: str, limit: int = 20) -> list[dict[str, Any]]:
    """DBから会話履歴を取得してClaude messages形式で返す。"""
    convs = db.get_recent_conversations(store_id, limit=limit)
    messages = []
    for c in convs:
        if c.role in ("user", "assistant"):
            messages.append({"role": c.role, "content": c.content})
    return messages


def append_message(store_id: str, role: str, content: str) -> None:
    """会話をDBに保存する。"""
    db.save_message(store_id=store_id, role=role, content=content)
