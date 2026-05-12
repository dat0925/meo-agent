# GBP Marketing Agent

LINE × Claude × Google Business Profile で店舗集客を自動化するAIエージェント。

## クイックスタート（モック動作）

```bash
# 1. リポジトリをクローン
git clone https://github.com/dat0925/meo-agent.git
cd meo-agent

# 2. 依存パッケージをインストール
pip install -e .

# 3. 環境変数を設定（ANTHROPIC_API_KEYのみ必須）
cp .env.example .env
# .envを編集して ANTHROPIC_API_KEY を設定

# 4. サーバー起動
uvicorn src.main:app --reload --port 8000

# 5. ブラウザでチャットUIを開く
# http://localhost:8000/mock/ui
```

## エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/mock/ui` | ブラウザテスト用チャットUI |
| POST | `/mock/chat` | モックチャットAPI（JSON） |
| POST | `/webhook/line` | LINE Webhook（本番） |
| POST | `/jobs/review-check` | 口コミ監視ジョブ手動実行 |
| POST | `/jobs/post-reminder` | 投稿催促ジョブ手動実行 |
| POST | `/jobs/photo-audit` | 写真監査ジョブ手動実行 |
| GET | `/health` | ヘルスチェック |

## 会話例

- 「未返信の口コミを見せて」→ 一覧表示＋返信文提案
- 「最近の投稿状況は？」→ 最終投稿日＋投稿案提案
- 「先月のアクセスデータを教えて」→ KPIサマリー
- 「投稿案を3つ作って」→ 文案3案を提示
- 「review-001に返信して」→ 返信文を生成・投稿

## モック→本番切り替え

| コンポーネント | モック | 本番 |
|------------|------|------|
| DB | `src/db/supabase.py`（インメモリ） | supabase-pyに差し替え |
| GBP API | ダミーデータ | `src/gbp/client.py` の `MOCK_MODE=false` |
| LINE | コンソール出力 | `LINE_CHANNEL_SECRET` + `LINE_CHANNEL_ACCESS_TOKEN` を設定 |

## 技術スタック

- **API**: FastAPI + uvicorn
- **AI**: Claude claude-sonnet-4-20250514 (Tool Calling)
- **DB**: Supabase (本番) / インメモリ (モック)
- **外部API**: Google Business Profile API v4.9
- **チャット**: LINE Messaging API
- **インフラ**: Cloud Run + Cloud Scheduler
