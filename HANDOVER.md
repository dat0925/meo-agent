# MEOコンシェルジュ — 引き継ぎ書

> **対象リポジトリ**: `dat0925/meo-agent`  
> **公開URL**: https://agt.taskra.jp  
> **最終更新**: 2026-06-02  
> **作成者**: AI Intern (Claude)

---

## 目次

1. [プロジェクト概要](#1-プロジェクト概要)
2. [技術スタック・インフラ](#2-技術スタックインフラ)
3. [ファイル構成](#3-ファイル構成)
4. [実装済み機能一覧](#4-実装済み機能一覧)
5. [【実装済み】クイックボタン UI A/B 切り替え](#5-実装済みクイックボタン-ui-ab-切り替え)
6. [【未実装・要対応】業種別 AI プロンプト最適化](#6-未実装要対応業種別-ai-プロンプト最適化)
7. [システムプロンプトの設計思想](#7-システムプロンプトの設計思想)
8. [主要な関数・処理の解説](#8-主要な関数処理の解説)
9. [デプロイ手順](#9-デプロイ手順)
10. [既知の制約・注意事項](#10-既知の制約注意事項)

---

## 1. プロジェクト概要

LINE UI 風のチャット画面から、店舗オーナーが Google ビジネスプロフィール（GBP）を AIと会話しながら管理できるデモアプリ。

**想定ユーザー**: 飲食店・美容室・建築リフォーム業などの中小店舗オーナー  
**主な操作**: 口コミへの返信生成・GBP投稿の作成・写真アップロード・データ確認  
**現状**: デモ（モックデータ）。Supabase Edge Functions 経由で Claude API を呼び出す。

---

## 2. 技術スタック・インフラ

| 区分 | 内容 |
|---|---|
| フロントエンド | Vanilla JS シングルファイル (`index.html`) |
| ホスティング | Cloudflare / カスタムドメイン `agt.taskra.jp` |
| AI モデル | Claude Sonnet（`claude-sonnet-4-20250514`） |
| AI プロキシ | Supabase Edge Functions `claude-proxy` |
| 画像生成 | Supabase Edge Functions `image-gen`（gpt-image-1）|
| リポジトリ | GitHub `dat0925/meo-agent` |
| ブランチ | `main` |

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
├── Dockerfile        ← （現状未使用）
├── README.md
├── pyproject.toml
└── src/              ← （現状未使用）
    └── supabase/     ← Edge Functions のソース（別管理）
```

`index.html` の内部構成（コメントブロックで分割されている）:

```
<style>            CSS（変数定義 → 各コンポーネントのスタイル）
<body>
  PIN認証モーダル
  チャット画面コンテナ
    ヘッダー
    メッセージエリア
    クイックボタン（デザインA / デザインB）
    入力エリア
    基本設定パネル（スライドイン）
    写真ソース選択シート
    投稿案タイプ選択シート
    苦情対応モーダル
<script>
  PIN認証ロジック
  モックデータ（STORE / reviews / posts）
  ツール定義（TOOLS 配列）
  executeTool() — ツール実行モック
  Claude API 呼び出し（callClaude）
  メッセージ描画（addMessage）
  承認フロー（showApprovalCard / approveAction）
  設定パネル操作
  写真・投稿シート操作
  デザイン切り替え（setDesign）
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
| GBP 投稿作成 | テキストのみ / AI 画像+テキストの 2 モード |
| 写真アップロード | AI 生成 / ライブラリ / カメラの 3 ソース |
| AI 画像生成 | gpt-image-1 で店舗用画像を生成 |
| 店舗情報変更 | 住所・営業時間など、承認フロー付き |
| データ確認 | GBP インサイト・キーワード順位・月次レポート |
| 承認フロー | 投稿・返信・写真・情報変更の 4 アクションに確認カード |
| 基本設定パネル | 店舗名・GBP ロケーションID・計測キーワード・計測地点 |
| クイックボタン A/B | UI 切り替えトグル（後述） |

---

## 5. 【実装済み】クイックボタン UI A/B 切り替え

### 概要

ヘッダー右上の **A / B トグル** で 2 種類のクイックボタン UI を切り替えられる。選択は `localStorage` に保存される。

### デザイン A（現行）

- 5×2 グリッド
- 絵文字アイコン + 短縮ラベル（2 行）
- 全機能を均等な視覚的重みで並列表示

### デザイン B（改修版）

- **機能をグループで整理**
  - 「返信・投稿」グループ：未返信口コミ・苦情対応・投稿案作成・写真投稿・店舗情報変更
  - 「データ確認」グループ：アクセスデータ・キーワード順位・月次レポート・投稿状況・基本設定
- SVG アイコン（Lucide 相当のアウトラインアイコン）+ ラベル + サブ説明テキスト付きの横長ボタン
- 苦情対応にアンバー（警告色）のアイコン背景

### 実装の場所

```
CSS   : .design-toggle / .qb-* クラス群（l.275〜340付近）
HTML  : id="quickBtns"（デザインA）/ id="quickBtnsB"（デザインB）
JS    : setDesign(d) 関数 / currentDesign 変数 / DOMContentLoaded内の setDesign() 呼び出し
Badge : updateReviewBadge() で A/B 両方のバッジを同期
```

### 切り替えロジック

```js
function setDesign(d) {
  // d = 'A' | 'B'
  // quickBtns     に .hidden を付け外し
  // quickBtnsB    に .visible を付け外し
  // toggleA/B ボタン に .active を付け外し
  // localStorage('meo_design') に保存
}
```

---

## 6. 【未実装・要対応】業種別 AI プロンプト最適化

### 背景と課題

現状のシステムプロンプトは「焼肉 大将」専用のハードコードされた文字列。業種が異なると AI の提案トーンや重点ポイントがズレる。

**ズレの原因は 3 層ある：**

| レイヤー | 問題 |
|---|---|
| コンテキスト不足 | 業種が AI に伝わっていない |
| トーン不一致 | 高級店 / カジュアル店 / 専門業者で文体が違う |
| 業界固有ルール | 業種特有の禁止表現・重要訴求が未定義 |

---

### 実装方針（設計提案）

#### 設定画面に追加する 5 項目

追加場所：`id="settingsPanel"` 内の `.settings-body` 先頭に新セクション追加

| 項目 | UI | 保存キー |
|---|---|---|
| 業種 | セレクトボックス or チップ選択（3〜5択） | `genre` |
| キャラクター（口調） | スライダー or 3択ラジオ | `tone` |
| 推しポイント | テキスト入力（1行） | `appealPoint` |
| NG ワード | タグ入力（複数） | `ngWords` |
| よく使うフレーズ | タグ入力（複数） | `preferredPhrases` |

#### 業種の選択肢と対応プリセット

```js
const GENRE_PRESETS = {
  restaurant: {
    label: '飲食店',
    systemAddition: `
業種: 飲食店
重点訴求: 季節感・食材の産地・雰囲気・予約のしやすさ
口コミ返信で必ず含める: 再来店への感謝、具体的なメニュー名
NGワード: 「値段が高い」への直接反論、過度な割引訴求
写真投稿テーマ: 料理・内観・季節イベント・スタッフ`,
    defaultKeywords: ['近隣地名＋業種', 'ランチ', '個室', '記念日'],
  },
  beauty: {
    label: '美容室・サロン',
    systemAddition: `
業種: 美容室・サロン
重点訴求: スタッフの技術・再来店率・カウンセリングの丁寧さ
口コミ返信で必ず含める: 担当スタッフへの感謝、次回予約への誘導
NGワード: 価格交渉への直接回答、曖昧な施術効果の約束
写真投稿テーマ: スタイル・内装・スタッフ・使用薬剤ブランド`,
    defaultKeywords: ['ヘアカット', 'カラー', 'パーマ', '近隣地名＋美容室'],
  },
  reform: {
    label: '建築・リフォーム',
    systemAddition: `
業種: 建築・リフォーム業
重点訴求: 施工実績・安心感・アフターサポート・対応エリア
口コミ返信で必ず含める: 施工への感謝、品質保証・アフターの言及
NGワード: 曖昧な工期約束、価格の断言、競合他社への言及
写真投稿テーマ: 施工前後・現場作業・完成写真・スタッフ`,
    defaultKeywords: ['リフォーム', '外壁塗装', '水回り', '近隣地名＋リフォーム'],
  },
  // 拡張例: medical / retail / fitness など
};
```

#### `appSettings` の拡張

```js
// 現状（localStorage キー: 'meo_settings'）
let appSettings = {
  storeName: '焼肉 大将',
  storeId: '',
  keywords: [...],
  locations: [...],
  // ↓ 以下を追加
  genre: 'restaurant',      // 'restaurant' | 'beauty' | 'reform'
  tone: 'friendly',         // 'formal' | 'friendly' | 'casual'
  appealPoint: '',          // 自由記述
  ngWords: [],              // string[]
  preferredPhrases: [],     // string[]
};
```

#### `SYSTEM_PROMPT` の動的生成

現状はハードコードされた定数。以下のように関数化する：

```js
function buildSystemPrompt(settings) {
  const preset = GENRE_PRESETS[settings.genre] || GENRE_PRESETS.restaurant;
  const toneDesc = {
    formal:   '丁寧語・敬語を基本とし、プロフェッショナルな印象を与える文体',
    friendly: '親しみやすく、絵文字を適度に使った読みやすい文体',
    casual:   'カジュアルで話しかけるような文体。常体も可',
  }[settings.tone] || '';

  const ngSection = settings.ngWords?.length
    ? `\n## 絶対に使わない表現\n${settings.ngWords.map(w => `- 「${w}」`).join('\n')}`
    : '';

  const phraseSection = settings.preferredPhrases?.length
    ? `\n## よく使うフレーズ（積極的に使う）\n${settings.preferredPhrases.map(p => `- 「${p}」`).join('\n')}`
    : '';

  const appealSection = settings.appealPoint
    ? `\n店舗の強み・推しポイント: ${settings.appealPoint}`
    : '';

  return `あなたは「MEOコンシェルジュ」です。
店舗オーナーの相棒として、Google ビジネスプロフィール（GBP）の管理を全面的にサポートします。

担当店舗: ${settings.storeName}
${preset.systemAddition}
${appealSection}

## 文体・口調
${toneDesc}
${ngSection}
${phraseSection}

## できること
（既存のシステムプロンプトの「できること」以降をここに続ける）
...`;
}
```

呼び出し元（`callClaude` 内）を以下に変更：

```js
// 変更前
body: JSON.stringify({ ..., system: SYSTEM_PROMPT, ... })

// 変更後
body: JSON.stringify({ ..., system: buildSystemPrompt(appSettings), ... })
```

#### 設定パネルの UI 追加箇所

`id="settingsPanel"` 内、現在の `<!-- 店舗情報 -->` セクションの**直前**に以下を挿入：

```html
<div class="settings-section">
  <div class="settings-section-title">AIの動作設定</div>

  <!-- 業種 -->
  <div class="settings-row">
    <label>業種</label>
    <div class="genre-chips" id="genreChips">
      <button class="genre-chip selected" data-genre="restaurant" onclick="selectGenre(this)">🍽 飲食店</button>
      <button class="genre-chip" data-genre="beauty" onclick="selectGenre(this)">💇 美容室</button>
      <button class="genre-chip" data-genre="reform" onclick="selectGenre(this)">🏠 建築・リフォーム</button>
    </div>
  </div>

  <!-- 口調 -->
  <div class="settings-row">
    <label>口調</label>
    <div class="tone-btns" id="toneBtns">
      <button class="tone-btn" data-tone="formal" onclick="selectTone(this)">丁寧</button>
      <button class="tone-btn selected" data-tone="friendly" onclick="selectTone(this)">フレンドリー</button>
      <button class="tone-btn" data-tone="casual" onclick="selectTone(this)">カジュアル</button>
    </div>
  </div>

  <!-- 推しポイント -->
  <div class="settings-row">
    <label>推しポイント</label>
    <input class="settings-input" id="sAppealPoint" placeholder="例：創業30年の老舗、個室完備">
  </div>

  <!-- NGワード -->
  <div class="settings-section-title">NGワード</div>
  <div class="keyword-list" id="ngWordList"></div>
  <div class="add-kw-row">
    <input id="newNgWord" placeholder="NGワードを追加" onkeydown="if(event.key==='Enter')addNgWord()">
    <button class="add-kw-btn" onclick="addNgWord()">追加</button>
  </div>

  <!-- よく使うフレーズ -->
  <div class="settings-section-title">よく使うフレーズ</div>
  <div class="keyword-list" id="preferredPhraseList"></div>
  <div class="add-kw-row">
    <input id="newPreferredPhrase" placeholder="フレーズを追加" onkeydown="if(event.key==='Enter')addPreferredPhrase()">
    <button class="add-kw-btn" onclick="addPreferredPhrase()">追加</button>
  </div>
</div>
```

対応する JS 関数:

```js
function selectGenre(el) {
  document.querySelectorAll('.genre-chip').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  appSettings.genre = el.dataset.genre;
}
function selectTone(el) {
  document.querySelectorAll('.tone-btn').forEach(b => b.classList.remove('selected'));
  el.classList.add('selected');
  appSettings.tone = el.dataset.tone;
}
function addNgWord() { /* addKeyword と同パターン */ }
function addPreferredPhrase() { /* addKeyword と同パターン */ }
```

---

## 7. システムプロンプトの設計思想

Claude に渡す `system` プロンプトの構造と意図：

```
## できること        → ツール一覧（AI が何を使えるか把握させる）
## AI画像生成の対応  → フロー手順（3 ステップを明示）
## 写真受信時の対応  → フロー手順
## 店舗情報変更の対応→ フロー手順
## 重要：承認フロー  → 「二重確認を禁止」する指示（UI が自動で挟むため）
## 行動原則          → LINE での読みやすさを意識した箇条書き
## 返答スタイル      → 口コミ返信文は「」で囲む等の出力フォーマット
```

**ポイント**: `reply_to_review` などの破壊的操作は UI 側が承認カードを自動挿入するため、AI 側で「承認しますか？」と聞くと二重になる。`重要：承認フローについて` セクションでこれを明示的に禁止している。

---

## 8. 主要な関数・処理の解説

### `callClaude(userMessage, imageBase64, imageMime)`

Claude API を最大 6 ラウンドのツール呼び出しループで呼ぶ。

```
ループ内:
  stop_reason === 'tool_use'   → executeTool() でモック実行 → tool_result を messages に追加 → 再度 API 呼び出し
  stop_reason === 'end_turn'   → テキストを返して終了
```

### `executeTool(name, input)`

全ツールのモック実装。本番化時はここを実際の GBP API / Supabase への呼び出しに置き換える。

承認が必要なツール（`APPROVAL_REQUIRED` Set に含まれるもの）は、`showApprovalCard()` で Promise を作り、ユーザーが承認/キャンセルするまで `await` で待機する。

### `buildSystemPrompt(settings)` ← 未実装

業種・口調・推しポイント・NGワード・よく使うフレーズを受け取り、動的にシステムプロンプトを生成する。[セクション6](#6-未実装要対応業種別-ai-プロンプト最適化) 参照。

---

## 9. デプロイ手順

```bash
# 1. クローン（PAT埋め込み）
git clone https://<PAT>@github.com/dat0925/meo-agent.git

# 2. index.html を編集

# 3. コミット＆プッシュ
cd meo-agent
git add index.html
git commit -m "feat: 変更内容"
git push origin main
```

ホスティングは Cloudflare Pages（または GitHub Pages 経由）。  
`main` ブランチへの push で自動デプロイされる。

---

## 10. 既知の制約・注意事項

| 制約 | 詳細 |
|---|---|
| 全データがモック | `STORE` / `reviews` / `posts` はすべてメモリ上の JS オブジェクト。リロードでリセットされる |
| 会話履歴はメモリのみ | `conversationHistory` はページリロードで消える |
| `localStorage` の用途 | PIN 認証トークン・設定・デザイン切り替え状態の 3 種のみ |
| AI 画像生成は gpt-image-1 | Supabase の `image-gen` Function 経由。OpenAI API キーが必要 |
| PIN は 2759 | `PIN_CONFIG.hash` に PBKDF2 ハッシュで保存。変更時は再ハッシュが必要 |
| 本番化時に要差し替え | `executeTool()` 内の全ツール → 実際の GBP API 呼び出しに置き換え |
| デザインB の `wheel` イベント | デザインA の `id="quickBtns"` にのみ登録されているため、B 側は不要（スクロール不要なレイアウトのため） |
