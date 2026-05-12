"""
LINE Messaging API ハンドラ。
MOCK_MODE=true の場合は署名検証をスキップする。
"""
from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any

import httpx

from src.db.models import LineWebhookBody

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"


def verify_signature(body_bytes: bytes, x_line_signature: str) -> bool:
    """LINE Webhook署名を検証する。MOCK_MODE時はスキップ。"""
    if MOCK_MODE:
        return True
    if not LINE_CHANNEL_SECRET:
        return False
    digest = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"),
        body_bytes,
        hashlib.sha256,
    ).digest()
    import base64
    expected = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected, x_line_signature)


def parse_webhook(body: dict[str, Any]) -> LineWebhookBody:
    return LineWebhookBody(**body)


def extract_text_message(event: dict[str, Any]) -> str | None:
    """Webhookイベントからテキストメッセージを取り出す。"""
    if event.get("type") != "message":
        return None
    msg = event.get("message", {})
    if msg.get("type") != "text":
        return None
    return msg.get("text")


def extract_user_id(event: dict[str, Any]) -> str:
    return event.get("source", {}).get("userId", "unknown")


def extract_reply_token(event: dict[str, Any]) -> str:
    return event.get("replyToken", "")


async def send_reply(reply_token: str, text: str) -> bool:
    """LINE Reply APIで返信を送る。MOCK_MODE時はログ出力のみ。"""
    if MOCK_MODE:
        print(f"[LINE MOCK REPLY] {text[:100]}...")
        return True
    if not LINE_CHANNEL_ACCESS_TOKEN:
        return False
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text[:5000]}],
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            LINE_REPLY_URL,
            json=payload,
            headers={"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"},
        )
    return resp.status_code == 200
