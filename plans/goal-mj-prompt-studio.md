# MJ Prompt Studio Goal Plan

## 目的

添付の開発指示書を正本、AGENTS.mdを作業規範として、PySide6製デスクトップアプリ `MJ Prompt Studio` のTask 1〜Task 8を順番に完遂する。アプリはプロンプト設計、語彙補助、検証、参照管理、実験計画、手動インポート結果レビュー、手動コピー支援、制作ログ管理に限定する。

## 非目標

- 画像生成サービス本体の自動操作、ログイン自動化、Cookie/Token/Session取得、非公式API、自動投稿。
- ユーザー向けUI、エクスポート、ログ、ヘルプに特定のMidjourneyモデルバージョン番号を表示すること。
- 実OpenAI APIキーがない環境で実API通信まで検証すること。
- ピクセル完全な参考UI画像再現。

## 対象範囲

- `src/mj_prompt_studio/` 配下のPySide6アプリ、Domain/Application/Infra/LLM/UI。
- SQLite永続化、asset store、settings、secret access境界。
- OpenAI Responses APIアダプタ、Structured Outputs schema、モックLLM、Job Queue。
- Composer、Free Editor、Matrix Lab、Reference Library、Result Review、Settings。
- README、docs、テスト、Makefile、パッケージング準備。

## 前提と仮定

- 既存リポジトリは初期状態で、`AGENTS.md`のみが追跡済み。
- 開発指示書の既定モデル名は設定値として保持し、UIやAgentへ直書きしない。
- APIキー未設定時はモックLLMを標準にし、主要フローをローカルで確認できるようにする。
- 添付UI画像は3ペイン、ダークテーマ、情報密度、タブ構成の参考とし、文言は開発指示書とAGENTS.mdを優先する。

## Goal 完了条件

- [x] Task 1〜Task 8の受け入れ条件がすべてDoneまたは明確なBlockedとして整理されている。
- [x] `make lint`、`make typecheck`、`make test`、`make build`の結果が記録されている。
- [x] README、docs、planが実装内容と整合している。
- [x] ユーザー向けUI文字列にMidjourneyの具体的なバージョン番号が混入しないテストが通る。
- [x] 不要ファイル、APIキー、DB、キャッシュ、ログ、ユーザー画像がgit追跡対象になっていない。

## マイルストーン

- [x] Task 1: アプリ基盤、UIシェル、Ruleset基盤、永続化を実装する。
- [x] Task 2: OpenAI API統合、LLM Orchestrator、Job Queue、Structured Outputs基盤を実装する。
- [x] Task 3: Composer、AI Brief、PromptDocument、Prompt Compilerを実装する。
- [x] Task 4: Prompt Doctor、Parameter Advisor、Vocabulary Agent、Validatorを実装する。
- [x] Task 5: Reference Library、画像解析、参照モード判定、語彙抽出を実装する。
- [x] Task 6: Matrix Lab、実験計画、Variant生成、CSV/Markdown Exportを実装する。
- [x] Task 7: Result Review、画像評価、改善サイクル、Final Auditorを実装する。
- [x] Task 8: 品質仕上げ、テスト、パッケージング、開発者ドキュメントを実装する。

## 受け入れ条件

- [x] アプリがPySide6で起動し、ダークテーマの3ペイン構成を表示する。
- [x] 新規プロジェクト、PromptDocument、revision、reference、matrix、result reviewが保存・再読込できる。
- [x] `Standard Ruleset`をresourcesから読み込み、UIはdisplay_nameのみ表示する。
- [x] LLM Jobは非同期実行され、APIキーなしではモックLLMで主要フローが動く。
- [x] Structured Outputs相当のJSON schema検証を通った結果だけがApplication Serviceに渡る。
- [x] AI BriefからPrompt Blocks、Compiled Prompt、Validation、Prompt Doctor/Parameter Advisor/Vocabulary提案まで接続される。
- [x] Reference Libraryで画像を手動取り込みし、解析結果と抽出語彙を保存できる。
- [x] Matrix Labで実験計画、variant、CSV/Markdown export、履歴保存ができる。
- [x] Result Reviewで画像評価、比較、改善候補、ComposerへのPatch返却、Final Auditができる。
- [x] README、docs、テスト、packaging準備が整う。

## 検証コマンド

- `make lint`
- `make typecheck`
- `make test`
- `make build`
- `make run`

## 既知 blocker

- なし。GUIの常駐起動は自動検証では `pytest` のUI smoke testで代替し、手動起動は `make run` で行う。

## feature flag / rollback

- OpenAI実API利用は `MJPS_LLM_MODE=real` とAPIキー設定時のみ有効化する。未設定時はmockへ戻る。
- Privacy modeではResponses APIの`store`をfalseにし、`previous_response_id`を使わない。
- 変更はTask範囲付きコミット単位でrevertできるようにする。

## 検証記録

| 日時 | コマンド | 結果 | メモ |
|---|---|---|---|
| 2026-05-24 | `.venv/bin/python -m pip install -e ".[dev]"` | Done | PySide6、OpenAI SDK、pydantic、pytest、ruff、mypyをローカルvenvへ導入 |
| 2026-05-24 | `make lint` | Done | ruff: All checks passed |
| 2026-05-24 | `make typecheck` | Done | mypy: no issues found in 52 source files |
| 2026-05-24 | `make test` | Done | pytest: 10 passed、UI smoke含む |
| 2026-05-24 | `make build` | Done | compileall成功 |
| 2026-05-24 | `.venv/bin/python scripts/verify_ui_text.py` | Done | 禁止UI文言なし |
| 2026-05-24 | `find . -maxdepth 3 ...` | Done | git対象外のmypy cache以外にDB、log、画像、envなし |
