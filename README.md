# MJ Prompt Studio

MJ Prompt Studioは、画像生成向けプロンプトの設計、語彙補助、検証、参照管理、実験計画、生成結果レビューを支援するローカルデスクトップアプリです。生成サービス本体の自動操作は行わず、ユーザーが手動でコピー、貼り付け、画像取り込みを行う前提です。

## 一般使用者向けガイド

- [Quick Start for Users](docs/quick-start.md): 初めて使うときの最短手順。
- [ユーザーマニュアル](docs/user-manual.md): 目的別に、どの画面で何をすればよいかを説明した利用者向けマニュアル。

## セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

APIキーがない場合でも、既定ではモックLLMで主要フローを確認できます。端末の環境変数 `OPENAI_API_KEY` にAPIキーがある場合は、起動時に自動で実API利用に切り替わります。

```bash
export OPENAI_API_KEY="..."
```

明示的にサンプル応答で起動したい場合だけ、`MJPS_LLM_MODE=mock` を指定します。

## 起動

```bash
make run
```

## 検証

```bash
make lint
make typecheck
make test
make build
make package
```

## 主な機能

- Composer: 日本語ブリーフからPromptDocument、Prompt Blocks、Compiled Promptを作成。
- Composer / Free Editor: 各入力欄のAI補完、候補、専門語化、短縮、説明、入力停止後の自動提案、Undo/Redo。
- Prompt Doctor: 決定論的ValidatorとAIレビューで矛盾、不足、弱い語彙を検出し、確認後にPatch適用。
- Parameter Advisor: Rulesetに基づくパラメータ表示と目的別提案、確認付き適用。
- Reference Library: 参照画像を手動取り込みまたはドラッグ&ドロップし、プレビュー、ローカル画像メタデータ、用途判定、検索、タグ、語彙抽出を保存。
- Matrix Lab: 実験目的からvariantを生成し、選択コピー、一括コピー、CSV/Markdownで出力。
- Result Review: 手動取り込み画像を元プロンプトと比較し、画像プレビュー、parameters snapshot、改善候補をComposerへPatchとして戻す。
- Export: Prompt only、Markdown record、JSON snapshot、CSV/Markdown matrix variants。
- Jobs: LLM処理の状態表示、キャンセル、再実行。

## 禁止事項

- 生成サービスのWeb、Discord、Botの自動操作。
- ログイン自動化、Cookie、Token、Session取得。
- 非公式API、自動投稿、ブラウザ自動クリック。
- ユーザー向けUIやエクスポートに特定のMidjourneyモデルバージョン番号を表示すること。

## ローカルデータ

ローカルDB、asset、cache、log、export、API response dumpはgit追跡対象にしません。既定の保存先はOS標準のアプリデータ領域で、`MJPS_DATA_DIR` により上書きできます。

APIキーは環境変数を優先し、Settingsから保存する場合は利用可能なOS資格情報ストアへ保存します。資格情報ストアが使えない環境ではセッション内適用に限定します。

Settingsでは、AI Brief、語彙補助、Prompt Doctor、Reference Analysis、Matrix Lab、Result Reviewなどの機能ごとに、使用モデル、推論強度、語彙量を保存できます。既定はすべて `gpt-5.5` / `medium` / `標準` です。
