# MJ Prompt Studio

MJ Prompt Studioは、画像生成向けプロンプトの設計、語彙補助、検証、参照管理、実験計画、生成結果レビューを支援するローカルアプリです。React + TypeScript client と localhost Python API で動作し、生成サービス本体の自動操作は行いません。

## 一般使用者向けガイド

- [Quick Start for Users](docs/quick-start.md): 初めて使うときの最短手順。
- [ユーザーマニュアル](docs/user-manual.md): 目的別の利用手順。

## セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
make client-install
```

Node.js と npm が必要です。Apple Silicon で Python の architecture mismatch が出る場合は、Terminal の Rosetta 起動をオフにするか、`arch -arm64 python3 -m venv .venv` で venv を作り直してください。`make` は `.venv/bin/python` を優先して使います。

APIキーがない場合でも、既定ではMockLLMで主要フローを確認できます。端末の環境変数 `OPENAI_API_KEY` にAPIキーがある場合は、起動時に自動で実API利用に切り替わります。

```bash
export OPENAI_API_KEY="..."
```

明示的にサンプル応答で起動したい場合だけ、`MJPS_LLM_MODE=mock` を指定します。

## 起動

```bash
make run
```

`make run` は `http://127.0.0.1:8765` のローカルAPIと `http://127.0.0.1:5173` のReact clientを同時に起動します。APIだけ起動する場合は `make run-api`、clientだけ起動する場合は `make run-react` を使います。

## 検証

```bash
make lint
make typecheck
make test
make build
make client-lint
make client-typecheck
make client-test
make client-build
make e2e
make package
```

OpenAPI schemaを更新する場合は `make generate-openapi` を実行します。

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

## データとセキュリティ

- APIは既定でlocalhostにのみbindします。
- React clientはtyped API client経由でPython Application Serviceを呼びます。
- SQLite、asset store、settings、job queueが永続化の正本です。
- APIキーは環境変数を優先し、Settingsから保存する場合は利用可能なOS資格情報ストアへ保存します。資格情報ストアが使えない環境ではセッション内適用に限定します。
- Privacy modeではResponses APIの保存を無効化し、`previous_response_id` を送りません。
- ローカルDB、asset、cache、log、export、API response dumpはgit追跡対象にしません。

## 禁止事項

- 生成サービスのWeb、Discord、Botの自動操作。
- ログイン自動化、Cookie、Token、Session取得。
- 非公式API、自動投稿、ブラウザ自動クリック。
- ユーザー向けUIやエクスポートに特定のMidjourneyモデルバージョン番号を表示すること。
