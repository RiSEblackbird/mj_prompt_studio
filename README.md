# MJ Prompt Studio

MJ Prompt Studioは、画像生成向けプロンプトの設計、語彙補助、検証、参照管理、実験計画、生成結果レビューを支援するローカルデスクトップアプリです。生成サービス本体の自動操作は行わず、ユーザーが手動でコピー、貼り付け、画像取り込みを行う前提です。

## セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

APIキーがない場合でも、既定ではモックLLMで主要フローを確認できます。実APIを使う場合は環境変数を設定します。

```bash
export OPENAI_API_KEY="..."
export MJPS_LLM_MODE=real
```

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
```

## 主な機能

- Composer: 日本語ブリーフからPromptDocument、Prompt Blocks、Compiled Promptを作成。
- Prompt Doctor: 決定論的ValidatorとAIレビューで矛盾、不足、弱い語彙を検出し、確認後にPatch適用。
- Parameter Advisor: Rulesetに基づくパラメータ表示と目的別提案。
- Reference Library: 参照画像を手動取り込みまたはドラッグ&ドロップし、用途判定、検索、タグ、語彙抽出を保存。
- Matrix Lab: 実験目的からvariantを生成し、選択コピー、一括コピー、CSV/Markdownで出力。
- Result Review: 手動取り込み画像を元プロンプトと比較し、改善候補をComposerへPatchとして戻す。
- Jobs: LLM処理の状態表示、キャンセル、再実行。

## 禁止事項

- 生成サービスのWeb、Discord、Botの自動操作。
- ログイン自動化、Cookie、Token、Session取得。
- 非公式API、自動投稿、ブラウザ自動クリック。
- ユーザー向けUIやエクスポートに特定のMidjourneyモデルバージョン番号を表示すること。

## ローカルデータ

ローカルDB、asset、cache、log、export、API response dumpはgit追跡対象にしません。既定の保存先はOS標準のアプリデータ領域で、`MJPS_DATA_DIR` により上書きできます。
