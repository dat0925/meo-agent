"""
Claudeエージェントループ。
Tool Callingを使ってGBP操作を実行し、最終的な返答テキストを返す。
"""
from __future__ import annotations

import json
import os
from typing import Any

import anthropic

from src.agent import memory, prompts, tools
from src.db import supabase as db

MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1024
MAX_TOOL_ROUNDS = 5  # 無限ループ防止


def chat(line_user_id: str, user_message: str) -> tuple[str, list[str]]:
    """
    ユーザーメッセージを受け取り、エージェントループを回してテキスト返答を返す。
    Returns: (reply_text, list of tool names called)
    """
    store = db.get_store_by_line_user(line_user_id)
    if store is None:
        return "まだ店舗が連携されていません。GBP連携を行ってください。", []

    store_id = store.id
    location_id = store.gbp_location_id

    # 会話履歴を保存
    memory.append_message(store_id, "user", user_message)

    # 履歴をロード（直前に追加したメッセージ含む）
    messages = memory.load_history(store_id, limit=20)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    tool_names_called: list[str] = []

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=prompts.SYSTEM_PROMPT,
            tools=tools.TOOL_DEFINITIONS,
            messages=messages,
        )

        # ツール呼び出しがない場合 → 最終返答
        if response.stop_reason == "end_turn":
            reply = _extract_text(response.content)
            memory.append_message(store_id, "assistant", reply)
            return reply, tool_names_called

        # ツール呼び出しがある場合
        if response.stop_reason == "tool_use":
            # assistantメッセージをmessagesに追加
            messages.append({"role": "assistant", "content": response.content})

            # 各ツールを実行してtool_resultを収集
            tool_results: list[dict[str, Any]] = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                tool_names_called.append(block.name)
                result = tools.execute_tool(
                    tool_name=block.name,
                    tool_input=block.input,
                    store_id=store_id,
                    location_id=location_id,
                )
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })

            messages.append({"role": "user", "content": tool_results})
            continue

        # 予期しないstop_reason
        break

    reply = "申し訳ありません、処理中にエラーが発生しました。"
    memory.append_message(store_id, "assistant", reply)
    return reply, tool_names_called


def _extract_text(content: list[Any]) -> str:
    """レスポンスのcontentブロックからテキストを結合して返す。"""
    texts = [block.text for block in content if hasattr(block, "text")]
    return "\n".join(texts).strip()
