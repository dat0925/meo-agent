"""
Claude Tool Calling 定義。
各ツールは (store_id, **kwargs) を受け取り dict を返す。
"""
from __future__ import annotations

from typing import Any

from src.gbp import client as gbp_client
from src.gbp import photos as gbp_photos
from src.gbp import posts as gbp_posts
from src.gbp import reviews as gbp_reviews

# ---- ツール定義（Claude API tools パラメータ用）----

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "get_gbp_stats",
        "description": "GBPの集客データ（検索表示数・クリック数・写真閲覧数など）を取得します。",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_unanswered_reviews",
        "description": "未返信の口コミ一覧を取得します。",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "reply_to_review",
        "description": "指定した口コミにオーナー返信を投稿します。",
        "input_schema": {
            "type": "object",
            "properties": {
                "review_id": {"type": "string", "description": "返信する口コミのID"},
                "reply_text": {"type": "string", "description": "返信文"},
            },
            "required": ["review_id", "reply_text"],
        },
    },
    {
        "name": "create_gbp_post",
        "description": "GBPに投稿を作成・公開します。",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "投稿テキスト（1500文字以内）"},
                "cta_type": {
                    "type": "string",
                    "description": "CTAボタン種別（BOOK/ORDER/SHOP/LEARN_MORE/SIGN_UP/CALL）",
                },
                "cta_url": {"type": "string", "description": "CTAリンクURL"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "get_posts_history",
        "description": "過去のGBP投稿一覧と最終投稿日を取得します。",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "取得件数（デフォルト10）"},
            },
            "required": [],
        },
    },
    {
        "name": "generate_post_draft",
        "description": "業種・季節・テーマに合わせたGBP投稿案を複数生成します（AIが文案を作成、実際の投稿は create_gbp_post で行う）。",
        "input_schema": {
            "type": "object",
            "properties": {
                "theme": {"type": "string", "description": "投稿テーマ（例：週末セール、新メニュー、季節のおすすめ）"},
                "count": {"type": "integer", "description": "生成する案の数（デフォルト3）"},
            },
            "required": [],
        },
    },
    {
        "name": "generate_review_reply",
        "description": "口コミ内容に基づいた返信文を生成します（実際の投稿は reply_to_review で行う）。",
        "input_schema": {
            "type": "object",
            "properties": {
                "review_id": {"type": "string", "description": "返信文を生成する口コミのID"},
            },
            "required": ["review_id"],
        },
    },
    {
        "name": "upload_photo_to_gbp",
        "description": "写真をGBPに追加します（モックではダミー処理）。",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "写真カテゴリ（FOOD/INTERIOR/EXTERIOR/TEAM）",
                },
            },
            "required": [],
        },
    },
]


# ---- ツール実行ハンドラ ----

def execute_tool(tool_name: str, tool_input: dict[str, Any], store_id: str, location_id: str = "") -> Any:
    client = gbp_client.GBPClient(location_id=location_id)

    if tool_name == "get_gbp_stats":
        return client.get_stats()

    elif tool_name == "get_unanswered_reviews":
        return gbp_reviews.get_unanswered_reviews(store_id)

    elif tool_name == "reply_to_review":
        return gbp_reviews.post_reply(
            store_id=store_id,
            gbp_review_id=tool_input["review_id"],
            reply_text=tool_input["reply_text"],
        )

    elif tool_name == "create_gbp_post":
        return gbp_posts.create_post(
            store_id=store_id,
            text=tool_input["text"],
            cta_type=tool_input.get("cta_type", ""),
            cta_url=tool_input.get("cta_url", ""),
        )

    elif tool_name == "get_posts_history":
        return gbp_posts.get_posts_history(store_id, limit=tool_input.get("limit", 10))

    elif tool_name == "generate_post_draft":
        # Claudeが自身で文案を生成するツール（実際にはAgentが返す内容をそのまま渡す）
        # ここではモックとして固定文案を返す
        theme = tool_input.get("theme", "お店の魅力")
        count = tool_input.get("count", 3)
        drafts = [
            f"【{theme}】焼肉 大将では、黒毛和牛をリーズナブルにご提供しています🐄 ご家族・ご友人との特別なひとときに、ぜひお越しください！",
            f"🔥 {theme}キャンペーン開催中！期間限定でドリンク1杯無料サービス中。詳しくはお店にお問い合わせください。",
            f"✨ 焼肉 大将からのお知らせ：{theme}にぴったりのコースをご用意しました。ご予約はお電話またはWeb予約で承ります。",
        ]
        return {"drafts": drafts[:count], "theme": theme}

    elif tool_name == "generate_review_reply":
        from src.db import supabase as db
        pending = db.get_pending_reviews(store_id)
        target = next((r for r in pending if r.gbp_review_id == tool_input["review_id"]), None)
        if not target:
            return {"error": "口コミが見つかりません"}
        if target.star_rating >= 4:
            reply = f"この度は温かいご口コミをいただき、誠にありがとうございます！{target.reviewer_name}様にまたお越しいただけることを、スタッフ一同心よりお待ちしております🙏"
        elif target.star_rating <= 2:
            reply = f"この度はご不満をおかけし、大変申し訳ございませんでした。{target.reviewer_name}様のご意見を真摯に受け止め、改善に努めてまいります。またの機会にぜひお試しいただけますと幸いです。"
        else:
            reply = f"ご来店いただき、誠にありがとうございます。{target.reviewer_name}様のご意見はスタッフ一同の励みとなっております。またのお越しを心よりお待ちしております。"
        return {"review_id": tool_input["review_id"], "suggested_reply": reply}

    elif tool_name == "upload_photo_to_gbp":
        return gbp_photos.upload_photo(
            store_id=store_id,
            image_bytes=b"",  # モックなので空バイト
            category=tool_input.get("category", "FOOD"),
        )

    else:
        return {"error": f"未知のツール: {tool_name}"}
