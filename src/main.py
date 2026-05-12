"""
FastAPIエントリポイント。

エンドポイント:
  POST /webhook/line       — LINE Webhook（本番）
  POST /mock/chat          — モックチャット（JSON API）
  GET  /mock/ui            — ブラウザテスト用チャットUI
  POST /jobs/review-check  — 口コミ監視ジョブ手動実行
  POST /jobs/post-reminder — 投稿催促ジョブ手動実行
  POST /jobs/photo-audit   — 写真監査ジョブ手動実行
  GET  /health             — ヘルスチェック
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

load_dotenv()

from src.agent import core as agent_core
from src.channel import line as line_handler
from src.db.models import MockChatRequest, MockChatResponse
from src.jobs import scheduler

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    mode = "MOCK" if MOCK_MODE else "PRODUCTION"
    print(f"🚀 GBP Marketing Agent 起動 [{mode} MODE]")
    yield


app = FastAPI(title="GBP Marketing Agent", lifespan=lifespan)


# ---- ヘルスチェック ----

@app.get("/health")
async def health():
    return {"status": "ok", "mock_mode": MOCK_MODE}


# ---- LINE Webhook ----

@app.post("/webhook/line")
async def line_webhook(
    request: Request,
    x_line_signature: str = Header(default=""),
):
    body_bytes = await request.body()
    if not line_handler.verify_signature(body_bytes, x_line_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    body = await request.json()
    webhook = line_handler.parse_webhook(body)

    for event in webhook.events:
        event_dict = event.model_dump()
        text = line_handler.extract_text_message(event_dict)
        if text is None:
            continue
        user_id = line_handler.extract_user_id(event_dict)
        reply_token = line_handler.extract_reply_token(event_dict)

        reply, _ = agent_core.chat(line_user_id=user_id, user_message=text)
        await line_handler.send_reply(reply_token=reply_token, text=reply)

    return {"status": "ok"}


# ---- モックチャット API ----

@app.post("/mock/chat", response_model=MockChatResponse)
async def mock_chat(req: MockChatRequest):
    reply, tool_calls = agent_core.chat(
        line_user_id=req.user_id,
        user_message=req.message,
    )
    return MockChatResponse(
        user_id=req.user_id,
        reply=reply,
        tool_calls=tool_calls,
    )


# ---- モックチャット UI ----

@app.get("/mock/ui", response_class=HTMLResponse)
async def mock_ui():
    return HTMLResponse(content=_CHAT_UI_HTML)


# ---- 監視ジョブ（手動トリガー）----

@app.post("/jobs/review-check")
async def job_review_check():
    result = await scheduler.run_review_check()
    return result


@app.post("/jobs/post-reminder")
async def job_post_reminder():
    result = await scheduler.run_post_reminder()
    return result


@app.post("/jobs/photo-audit")
async def job_photo_audit():
    result = await scheduler.run_photo_audit()
    return result


# ---- チャットUI HTML ----

_CHAT_UI_HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GBP Agent — モックチャット</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f0f2f5; display: flex; justify-content: center;
         align-items: center; min-height: 100vh; }
  .container { width: 100%; max-width: 480px; height: 100vh;
               display: flex; flex-direction: column; background: #fff;
               box-shadow: 0 0 24px rgba(0,0,0,.12); }
  .header { background: #06c755; color: white; padding: 16px 20px;
            font-size: 16px; font-weight: 700; display: flex;
            align-items: center; gap: 10px; }
  .header .badge { background: rgba(255,255,255,.25); border-radius: 6px;
                   padding: 2px 8px; font-size: 11px; font-weight: 500; }
  .messages { flex: 1; overflow-y: auto; padding: 16px;
              display: flex; flex-direction: column; gap: 12px; }
  .msg { display: flex; gap: 8px; align-items: flex-end; }
  .msg.user { flex-direction: row-reverse; }
  .bubble { max-width: 76%; padding: 10px 14px; border-radius: 18px;
            line-height: 1.6; font-size: 14px; white-space: pre-wrap;
            word-break: break-word; }
  .msg.bot .bubble { background: #f0f0f0; border-bottom-left-radius: 4px; }
  .msg.user .bubble { background: #06c755; color: white;
                      border-bottom-right-radius: 4px; }
  .avatar { width: 36px; height: 36px; border-radius: 50%;
            background: #06c755; display: flex; align-items: center;
            justify-content: center; font-size: 18px; flex-shrink: 0; }
  .tools { font-size: 11px; color: #888; margin-top: 4px;
           padding: 0 4px; }
  .loading .bubble { background: #f0f0f0; color: #aaa; font-style: italic; }
  .input-area { padding: 12px 16px; border-top: 1px solid #eee;
                display: flex; gap: 8px; align-items: center; }
  .input-area input { flex: 1; padding: 10px 14px; border: 1px solid #ddd;
                      border-radius: 22px; font-size: 14px; outline: none; }
  .input-area input:focus { border-color: #06c755; }
  .input-area button { background: #06c755; color: white; border: none;
                       border-radius: 50%; width: 42px; height: 42px;
                       font-size: 18px; cursor: pointer; flex-shrink: 0; }
  .input-area button:disabled { background: #ccc; cursor: default; }
  .quick-btns { padding: 8px 16px; display: flex; gap: 8px;
                overflow-x: auto; scrollbar-width: none; }
  .quick-btns::-webkit-scrollbar { display: none; }
  .quick-btn { white-space: nowrap; padding: 6px 14px; border: 1px solid #06c755;
               color: #06c755; border-radius: 16px; font-size: 13px;
               cursor: pointer; background: white; flex-shrink: 0; }
  .quick-btn:hover { background: #f0fff5; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    🤖 GBPコンシェルジュ
    <span class="badge">MOCK</span>
  </div>
  <div class="messages" id="messages">
    <div class="msg bot">
      <div class="avatar">🤖</div>
      <div>
        <div class="bubble">こんにちは！GBPコンシェルジュです😊
店舗「焼肉 大将」のGBP管理をサポートします。
口コミ返信・投稿作成・データ確認など、何でもお気軽にどうぞ！</div>
      </div>
    </div>
  </div>
  <div class="quick-btns" id="quickBtns">
    <button class="quick-btn" onclick="sendQuick('未返信の口コミを見せて')">📬 未返信口コミ</button>
    <button class="quick-btn" onclick="sendQuick('最近の投稿状況は？')">📝 投稿状況</button>
    <button class="quick-btn" onclick="sendQuick('先月のアクセスデータを教えて')">📊 データ確認</button>
    <button class="quick-btn" onclick="sendQuick('投稿案を3つ作って')">✍️ 投稿案作成</button>
    <button class="quick-btn" onclick="sendQuick('写真の状況は？')">📸 写真確認</button>
  </div>
  <div class="input-area">
    <input type="text" id="input" placeholder="メッセージを入力..."
           onkeydown="if(event.key==='Enter')sendMessage()"/>
    <button id="sendBtn" onclick="sendMessage()">➤</button>
  </div>
</div>
<script>
  const userId = 'mock_user_001';
  const messagesEl = document.getElementById('messages');
  const inputEl = document.getElementById('input');
  const sendBtn = document.getElementById('sendBtn');

  function scrollBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function addMessage(role, text, tools) {
    const wrap = document.createElement('div');
    wrap.className = 'msg ' + role;
    const bubble = '<div class="bubble">' + escHtml(text) + '</div>';
    const toolsHtml = (tools && tools.length)
      ? '<div class="tools">🔧 ' + tools.join(', ') + '</div>' : '';
    if (role === 'bot') {
      wrap.innerHTML = '<div class="avatar">🤖</div><div>' + bubble + toolsHtml + '</div>';
    } else {
      wrap.innerHTML = '<div>' + bubble + '</div>';
    }
    messagesEl.appendChild(wrap);
    scrollBottom();
    return wrap;
  }

  function escHtml(s) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;')
            .replace(/>/g,'&gt;').replace(/\\n/g,'\\n');
  }

  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;
    inputEl.value = '';
    sendBtn.disabled = true;

    addMessage('user', text);

    const loading = addMessage('bot', '入力中…');
    loading.classList.add('loading');

    try {
      const res = await fetch('/mock/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ user_id: userId, message: text }),
      });
      const data = await res.json();
      loading.remove();
      addMessage('bot', data.reply, data.tool_calls);
    } catch (e) {
      loading.remove();
      addMessage('bot', 'エラーが発生しました。サーバーの起動を確認してください。');
    }
    sendBtn.disabled = false;
    inputEl.focus();
  }

  function sendQuick(text) {
    inputEl.value = text;
    sendMessage();
  }
</script>
</body>
</html>
"""
