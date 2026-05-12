"""LINE通知送信。MOCK_MODEではコンソール出力のみ。"""
from __future__ import annotations

import os

import httpx

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"


async def push_message(line_user_id: str, text: str) -> bool:
    """LINEユーザーにPush通知を送る。"""
    if MOCK_MODE:
        print(f"[LINE MOCK PUSH → {line_user_id}] {text[:120]}")
        return True
    if not LINE_CHANNEL_ACCESS_TOKEN:
        return False
    payload = {
        "to": line_user_id,
        "messages": [{"type": "text", "text": text[:5000]}],
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            LINE_PUSH_URL,
            json=payload,
            headers={"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"},
        )
    return resp.status_code == 200
