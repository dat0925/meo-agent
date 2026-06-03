# MEOコンシェルジュ — 引き継ぎ書

> **対象リポジトリ**: `dat0925/meo-agent`  
> **公開URL**: https://agt.taskra.jp  
> **最終更新**: 2026-06-03  
> **作成者**: AI Intern (Claude)  
> **PINコード**: 2759

---

## 目次

1. [プロジェクト概要](#1-プロジェクト概要)
2. [技術スタック・インフラ](#2-技術スタックインフラ)
3. [ファイル構成](#3-ファイル構成)
4. [実装済み機能一覧](#4-実装済み機能一覧)
5. [クイックボタン UI — A/B 切り替え](#5-クイックボタン-ui--ab-切り替え)
6. [AIの動作設定 — 設定パネルと動的プロンプト](#6-aiの動作設定--設定パネルと動的プロンプト)
7. [システムプロンプトの設計思想](#7-システムプロンプトの設計思想)
8. [主要な関数・処理の解説](#8-主要な関数処理の解説)
9. [appSettings — 設定値の全スキーマ](#9-appsettings--設定値の全スキーマ)
10. [デプロイ手順](#10-デプロイ手順)
11. [既知の制約・注意事項](#11-既知の制約注意事項)
12. [今後の課題・拡張候補](#12-今後の課題拡張候補)

---

## 1. プロジェクト概要

LINE UI 風のチャット画面から、店舗オーナーが Google ビジネスプロフィール（GBP）を  
AI と会話しながら管理できるデモアプリ。

**想定ユーザー**: 飲食店・美容室・建築リフォーム業などの中小店舗オーナー  
**主な操作**: 口コミへの返信生成・GBP投稿の作成・写真アップロード・データ確認  
**現状**: フルデモ（モックデータ）。Supabase Edge Functions 経由で Claude API を呼び出す。  
**本番化**: `executeTool()` 内の全ツールを実際の GBP API 呼び出しに置き換えるだけで動く設計。

---

## 2. 技術スタック・インフラ

| 区分 | 内容 |
|---|---|
| フロントエンド | Vanilla JS シングルファイル（`index.html`）|
| ホスティング | Cloudflare Pages / カスタムドメイン `agt.taskra.jp` |
| AI モデル | Claude Sonnet（`claude-sonnet-4-20250514`）|
| AI プロキシ | Supabase Edge Functions `claude-proxy` |
| 画像生成 | Supabase Edge Functions `image-gen`（gpt-image-1）|
| リポジトリ | GitHub `dat0925/meo-agent` |
| ブランチ | `main`（push で自動デプロイ）|

### Supabase エンドポイント

```
claude-proxy : https://sfhtvtcmgueystyuhzvd.supabase.co/functions/v1/claude-proxy
image-gen    : https://sfhtvtcmgueystyuhzvd.supabase.co/functions/v1/image-gen
```

---

## 3. ファイル構成

```
meo-agent/
├── index.html        ← フロントエンド全体（HTML / CSS / JS を 1 ファイルに集約）
├── HANDOVER.md       ← 本ファイル
├── CNAME             ← agt.taskra.jp のドメイン設定
├── Dockerfile        ← 現状未使用
├── README.md
├── pyproject.toml
└── src/              ← 現状未使用（Edge Functions のソースは Supabase 側で別管理）
```

### `index.html` 内部構成

```
<style>
  CSS変数定義（カラー・フォント）
  PIN認証スタイル
  ヘッダー・チャットUI・メッセージバブル
  クイックボタン（デザインA / デザインB）
  設定パネル（基本設定 + AIの動作設定）
  ボトムシート（写真ソース / 投稿タイプ）
  苦情対応モーダル
  承認カード

<body>
  PIN認証モーダル
  チャット画面コンテナ
    ヘッダー（店舗名・デモバッジ・A/Bトグル・外部リンク）
    メッセージエリア
    クイックボタンエリア（デザインA / デザインB を並列配置）
    テキスト入力エリア
  基本設定パネル（スライドイン）
  写真ソース選択シート
  投稿案タイプ選択シート
  苦情対応モーダル

<script>
  PIN認証ロジック（PBKDF2ハッシュ・ロックアウト）
  モックデータ（STORE / reviews / posts）
  ツール定義（TOOLS 配列）
  executeTool() — ツール実行（モック実装）
  GENRE_PRESETS / TONE_PRESETS / TARGET_LABELS / RESPONDER_LABELS
  buildSystemPrompt() — 設定値から動的にシステムプロンプトを生成
  callClaude() — Claude API 呼び出しループ
  addMessage() / addLoading() — メッセージ描画
  showApprovalCard() / approveAction() — 承認フロー
  設定パネル操作（openSettings / saveSettings / renderXxx）
  業種・口調・返信者・ターゲット選択関数
  写真・投稿シート操作
  setDesign() — A/B 切り替え
  DOMContentLoaded 初期化
```

---

## 4. 実装済み機能一覧

| 機能 | 説明 |
|---|---|
| PIN 認証 | 4 桁 PIN（PBKDF2 ハッシュ）。5 回失敗で 5 分ロック |
| チャット UI | LINE 風バブル、ボット/ユーザー・タイムスタンプ・ローディング |
| 口コミ返信 | 未返信一覧取得 → AI 返信文生成 → 承認後投稿 |
| 苦情対応モーダル | 口コミ貼り付け＋スタイルチップ選択 → 返信文生成 |
| GBP 投稿作成 | テキストのみ / AI 画像＋テキストの 2 モード |
| 写真アップロード | AI 生成 / ライブラリ / カメラの 3 ソース |
| AI 画像生成 | gpt-image-1 で店舗用画像を生成 |
| 店舗情報変更 | 住所・営業時間など、承認フロー付き |
| データ確認 | GBP インサイト・キーワード順位・月次レポート |
| 承認フロー | 投稿・返信・写真・情報変更の 4 アクションに確認カード |
| クイックボタン A/B | ヘッダートグルで 2 種の UI を切り替え（localStorage 保存）|
| AIの動作設定 | 業種・業態補足・口調・返信者・ターゲット・推しポイント・NGワード・フレーズ |
| 動的システムプロンプト | `buildSystemPrompt()` が設定値を毎回合成して Claude に渡す |

---

## 5. クイックボタン UI — A/B 切り替え

ヘッダー右上の **A / B トグル** で 2 種類の UI を切り替える。`localStorage('meo_design')` に保存。

### デザイン A（現行・比較用）

- 5×2 グリッド、絵文字アイコン＋短縮ラベル
- 全 10 機能を均等な視覚的重みで並列表示

### デザイン B（メリハリ案・推奨）

視覚的重みを 3 段階に分けた設計：

| 段 | ボタン | 対象機能 |
|---|---|---|
| 大（グリーン塗り） | 1個 | 未返信の口コミ（バッジ付き）|
| 大（アウトライン） | 1個 | 投稿案を作成 |
| 中（アイコン＋ラベル） | 3個 | 苦情対応・写真を投稿・店舗情報 |
| 小（フラット） | 5個 | アクセス・順位・レポート・投稿状況・設定 |

```
CSS   : .qb-btn-primary / .qb-btn-secondary / .qb-btn-tertiary クラス群
HTML  : id="quickBtns"（A）/ id="quickBtnsB"（B）
JS    : setDesign(d)  d = 'A' | 'B'
Badge : updateReviewBadge() で A/B 両バッジを同期
```

---

## 6. AIの動作設定 — 設定パネルと動的プロンプト

### 設定項目（全 8 項目）

| 項目 | UI | `appSettings` キー | 説明 |
|---|---|---|---|
| 業種 | 2×2 チップ選択 | `genre` | `restaurant` / `beauty` / `reform` / `other` |
| 業態補足 | テキスト入力（業種選択後に表示） | `genreSub` | 「焼肉店」「ネイルサロン」など。`other` 時は必須 |
| 口調 | 3 択セグメント | `tone` | `formal` / `friendly` / `casual` |
| 口コミ返信の署名 | 3 択グリッド | `responder` | `owner` / `staff` / `shop` |
| スタッフ名 | テキスト入力（`staff` 選択時のみ表示） | `responderName` | 担当スタッフ名 |
| ターゲット客層 | 複数選択チップ（6 種） | `targetAudience` | `string[]` |
| 推しポイント | テキスト入力 1 行 | `appealPoint` | 自由記述 |
| NG ワード | タグ入力（複数） | `ngWords` | `string[]` |
| よく使うフレーズ | タグ入力（複数） | `preferredPhrases` | `string[]` |

### 業種プリセット（`GENRE_PRESETS`）

各業種に以下の 4 フィールドを持つ：

```js
{
  label: '飲食店',
  subPlaceholder: '例：焼肉店・居酒屋・ランチカフェ',   // 業態補足のplaceholder
  subHint: 'AIが業種に合わせた文章を生成するために...',  // 業態補足の説明文
  systemAddition: '業種: 飲食店\n重点訴求: ...',        // プロンプトに挿入される文字列
}
```

業種ごとの `systemAddition` の内容（プロンプトへの影響が大きい部分）：

| 業種 | 重点訴求 | 口コミ返信 | NG対応 |
|---|---|---|---|
| 飲食店 | 季節感・食材・雰囲気・予約しやすさ | 再来店感謝・メニューへの言及 | 値段への直接反論・割引訴求 |
| 美容室・サロン | 技術力・カウンセリング・再来店しやすさ | スタッフへの感謝・次回予約誘導 | 価格交渉・曖昧な施術効果 |
| 建築・リフォーム | 施工実績・アフターサポート・安心感 | 施工へのこだわり・品質保証 | 曖昧な工期・競合他社への言及 |
| その他 | （業態補足で補う） | — | — |

### `buildSystemPrompt(s)` の処理フロー

```
1. genre → GENRE_PRESETS から systemAddition を取得
2. genreSub → 「具体的な業態: ○○」として追記
3. tone → TONE_PRESETS から文体指示を取得
4. responder / responderName → 返信者の文章を生成
5. targetAudience → ターゲット客層の説明を生成
6. appealPoint → 「店舗の強み・推しポイント: ○○」として追記
7. ngWords → 「## 絶対に使わない表現」セクションを生成
8. preferredPhrases → 「## 積極的に使うフレーズ」セクションを生成
9. 固定セクション（できること / 承認フロー / 行動原則 / 返答スタイル）を連結
10. 改行結合して文字列として返す
```

呼び出し元（`callClaude()` 内）:

```js
body: JSON.stringify({
  model: 'claude-sonnet-4-20250514',
  max_tokens: 1024,
  system: buildSystemPrompt(appSettings),  // ← 毎回動的生成
  tools: TOOLS,
  messages,
})
```

### UI の動的挙動

| 操作 | 動く UI |
|---|---|
| 業種チップを選択 | 業態補足フィールドが出現。プレースホルダーとヒント文が業種に合わせて変わる |
| 業種「その他」を選択 | 業態補足フィールドに「＊必須」ラベルが表示される |
| 返信者「スタッフ名」を選択 | スタッフ名入力欄が展開される |

---

## 7. システムプロンプトの設計思想

```
店舗情報ブロック    → 業種・業態・推しポイント・ターゲットなど
口コミ返信・文体    → 口調指示・返信者指示・NGワード・よく使うフレーズ
## できること       → ツール一覧（AI が何を使えるか把握させる）
## AI画像生成の対応 → 3 ステップのフロー手順
## 写真受信時の対応 → 3 ステップのフロー手順
## 店舗情報変更の対応→ 3 ステップのフロー手順
## 重要：承認フロー → 「二重確認を禁止」する指示（UI が自動で挟むため）
## 行動原則         → LINE での読みやすさを意識した箇条書き
## 返答スタイル     → 「」で囲む等の出力フォーマット指示
```

**重要な設計判断**:  
`reply_to_review` など破壊的操作は UI 側が承認カードを自動挿入する。  
AI 側で「承認しますか？」と聞くと二重になるため、`重要：承認フローについて` セクションで明示的に禁止している。

---

## 8. 主要な関数・処理の解説

### `callClaude(userMessage, imageBase64, imageMime)`

Claude API を最大 6 ラウンドのツール呼び出しループで呼ぶ。

```
ループ:
  stop_reason === 'tool_use'
    → executeTool() でモック実行
    → tool_result を messages に追加
    → 再度 API 呼び出し（最大6回）
  stop_reason === 'end_turn'
    → テキストを返して終了
```

### `executeTool(name, input)`

全ツールのモック実装。本番化時はここを GBP API / Supabase 呼び出しに置き換える。

`APPROVAL_REQUIRED` Set に含まれるツール（`reply_to_review` など 4 種）は `showApprovalCard()` で Promise を生成し、ユーザーが承認/キャンセルするまで `await` で待機する。

### `buildSystemPrompt(s)`

`appSettings` を受け取り、設定値を文字列配列に組み立てて `join('\n')` して返す。  
テンプレートリテラルは **使わず** 文字列配列＋`join` で実装している（改行エスケープの不具合防止のため）。

### `setDesign(d)`

```js
// d = 'A' | 'B'
// - id="quickBtns"  に .hidden を付け外し
// - id="quickBtnsB" に .visible を付け外し
// - id="toggleA/B"  に .active を付け外し
// - localStorage('meo_design') に保存
```

### `updateReviewBadge()`

未返信口コミ数を `reviews` 配列から計算し、デザイン A・B 両方のバッジ（`reviewBadge` / `reviewBadgeB`）を同期更新する。

### `updateGenreSubUI(genre)`

業種チップ選択時に呼ばれる。  
業態補足フィールドの表示・プレースホルダー・ヒント・必須表示を `GENRE_PRESETS` から引いて更新する。

### `updateResponderNameUI(responder)`

返信者選択時に呼ばれる。`staff` 選択時のみスタッフ名入力欄（`responderNameWrap`）を表示する。

---

## 9. appSettings — 設定値の全スキーマ

`localStorage` キー: `'meo_settings'`

```js
const DEFAULT_SETTINGS = {
  // 店舗基本情報
  storeName: '焼肉 大将',
  storeId: '',                    // GBP ロケーションID
  keywords: ['焼肉 渋谷', ...],   // 計測キーワード
  locations: [{ name: '', address: '' }],  // 計測地点

  // AIの動作設定
  genre: 'restaurant',            // 'restaurant' | 'beauty' | 'reform' | 'other'
  genreSub: '焼肉店',             // 業態補足（自由記述）
  tone: 'friendly',               // 'formal' | 'friendly' | 'casual'
  responder: 'owner',             // 'owner' | 'staff' | 'shop'
  responderName: '',              // スタッフ名（responder === 'staff' の場合のみ使用）
  targetAudience: [],             // ('family'|'couple'|'business'|'solo'|'senior'|'young')[]
  appealPoint: '',                // 推しポイント（1行自由記述）
  ngWords: [],                    // string[] — AI が絶対に使わない言葉
  preferredPhrases: [],           // string[] — 積極的に使わせたいフレーズ
};

// 初期化（既存 localStorage とマージ）
let appSettings = Object.assign({}, DEFAULT_SETTINGS, JSON.parse(localStorage.getItem('meo_settings') || '{}'));
```

---

## 10. デプロイ手順

```bash
# 1. クローン（PAT 埋め込み）
git clone https://<PAT>@github.com/dat0925/meo-agent.git
cd meo-agent

# 2. index.html を編集

# 3. コミット＆プッシュ
git add index.html
git commit -m "feat: 変更内容"
git push origin main
# → Cloudflare Pages が自動デプロイ（反映まで約1分）
```

**注意**: このプロジェクトはスマートフォン/iPad からの開発を前提としており、  
CLI ツールは使用せず Claude との会話経由で全コード変更・push を行っている。

---

## 11. 既知の制約・注意事項

| 制約 | 詳細 |
|---|---|
| 全データがモック | `STORE` / `reviews` / `posts` はメモリ上の JS オブジェクト。リロードでリセットされる |
| 会話履歴はメモリのみ | `conversationHistory` はページリロードで消える |
| `localStorage` の用途 | PIN 認証トークン・設定（`meo_settings`）・デザイン選択（`meo_design`）の 3 種 |
| AI 画像生成 | Supabase `image-gen` Function 経由。OpenAI API キーが Supabase 側に必要 |
| PIN は 2759 | `PIN_CONFIG.hash` に PBKDF2 ハッシュで保存。変更時は再ハッシュが必要 |
| 本番化時の差し替え箇所 | `executeTool()` 内の全ツール → 実際の GBP API 呼び出しに置き換える |
| `buildSystemPrompt` の実装方針 | テンプレートリテラルを使わず文字列配列＋`join` で実装（改行エスケープ不具合の再発防止）|
| デザイン B の wheel イベント | デザイン A の `id="quickBtns"` にのみ登録（B はスクロール不要なレイアウトのため不要）|

---

## 12. 今後の課題・拡張候補

| 優先度 | 内容 | 備考 |
|---|---|---|
| 高 | `executeTool()` の本番化（GBP API 接続） | モックから実 API へ置き換えるだけで動く設計 |
| 高 | 会話履歴の永続化（Supabase or localStorage） | 現状リロードで消える |
| 中 | 業種プリセットの拡張（医療・小売・フィットネスなど） | `GENRE_PRESETS` にオブジェクトを追加するだけ |
| 中 | デザイン B を正式採用し、A/B トグルを削除 | ユーザーテスト後に判断 |
| 低 | 多店舗対応（店舗切り替え UI） | `appSettings` を配列化すれば対応可能 |
| 低 | 設定の共有・エクスポート機能 | 同一チェーン店への設定コピーなど |
