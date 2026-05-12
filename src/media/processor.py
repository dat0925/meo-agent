"""
画像処理。Pillowを使ってテキスト合成・リサイズを行う。
MOCK_MODE時は実際の加工を行わずダミーbytesを返す。
"""
from __future__ import annotations

import io
import os

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"


def add_text_overlay(image_bytes: bytes, text: str, position: str = "bottom") -> bytes:
    """画像にテキストを合成する。"""
    if MOCK_MODE:
        print(f"[MEDIA MOCK] テキスト合成: '{text[:30]}' ({position})")
        return image_bytes  # 加工せずそのまま返す

    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    draw = ImageDraw.Draw(img)
    font_size = max(24, img.width // 20)
    try:
        font = ImageFont.truetype("NotoSansJP-Bold.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    x = img.width // 2
    y = img.height - 80 if position == "bottom" else 40
    # 縁取り
    for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
        draw.text((x + dx, y + dy), text, font=font, fill="black", anchor="mm")
    draw.text((x, y), text, font=font, fill="white", anchor="mm")

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def resize_for_gbp(image_bytes: bytes) -> bytes:
    """GBP推奨サイズ（720×720以上）にリサイズする。"""
    if MOCK_MODE:
        return image_bytes

    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes))
    min_side = min(img.width, img.height)
    if min_side < 720:
        scale = 720 / min_side
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()
