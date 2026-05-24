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

## 再監査 2026-05-24

前回実装は縦切りの骨格として動く一方、運用可能レベルとして以下が不足していたため追加改修する。

- [x] AI Patchがユーザー確認なしに自動適用される問題を修正。
- [x] Job status UIにキャンセルと再実行を追加。
- [x] Reference Libraryにドラッグ&ドロップ、検索、タグ保存、削除確認、抽出語彙のComposer返却を追加。
- [x] Matrix Labに選択Variantコピーと一括コピーを追加。
- [x] Result Reviewに比較表示と改善候補のComposer Patch返却を追加。
- [x] ToolbarのOpen / Exportを実操作に変更。
- [x] Settingsにセッション内APIキー適用、Response Storage保存、接続テストを追加。
- [x] SQLite migration versionとresult review / reference削除の永続化テストを追加。
- [x] Structured Outputsのschema検証をPydanticで型検証するよう補強。

## 販売品質再監査 2026-05-24

添付開発指示書と6枚の参考画像を再確認し、顧客が制作サイクルを実運用する観点で以下を追加補強した。

- [x] Composer各Blockに `AI補完`、`候補`、`専門語化`、`短縮`、`説明` を追加。
- [x] 入力停止後の自動AI提案をdebounce付きでJob Queueへ流し、古い結果を破棄する。
- [x] Prompt Compiler AgentをCompile導線へ接続し、決定論的Compile後に非同期レビューを表示する。
- [x] ToolbarにUndo/Redoを追加し、PromptDocument状態をrevision付きで復元する。
- [x] Free Editorの変換ボタンをLLM Jobへ接続し、左右エディタとライブプレビューを実操作化する。
- [x] Parameter Advisorの目的入力、AI提案、確認付き適用を実装する。
- [x] 採用されたAI Patch語彙をUser Vocabulary Profileへ保存する。
- [x] Reference Libraryでローカル画像メタデータ、簡易カラーパレット、プレビュー、Reference Modeフィルターを表示する。
- [x] Result Reviewで画像プレビュー、Source Prompt、Parameters Snapshotを表示する。
- [x] ExportをPrompt only、Markdown record、JSON snapshot、CSV/Markdown matrix variantsへ拡張する。
- [x] Settings保存時にPrivacy modeを実行中設定へ反映し、OS資格情報ストアが使える場合のみAPIキーを保存する。
- [x] `make package` によるPython配布パッケージ作成入口を追加する。
- [x] 追加機能のUnit/UI smoke testを補強する。

## 機能別LLM設定追加 2026-05-24

OpenAI公式ドキュメントで `gpt-5.5`、`gpt-5.4-mini`、`gpt-5.4-nano` の位置づけを確認し、機能ごとの品質/速度調整をSettingsから保存できるようにする。

- [x] AI Brief、語彙補助、Prompt Compiler、Prompt Doctor、Parameter Advisor、Reference Analysis、Matrix Lab、Result Review、Final Auditごとにモデル、推論強度、語彙量を保存する。
- [x] 既定値は全機能 `gpt-5.5` / `medium` / `標準` とする。
- [x] 保存済み設定をSQLiteから起動時に復元し、Job Queueのmodel/reasoning表示と実Agent実行へ反映する。
- [x] MockLLMでも語彙量設定に応じて候補数が変わるようにする。
- [x] 一般使用者向けマニュアル、Quick Start、LLM docs、UI spec、READMEを更新する。
- [x] lint / typecheck / test / UI文言検査を再実行する。

## CIワークフロー追加 2026-05-25

Pull Requestと主要ブランチへのpushで、ローカル検証入口と同等の品質ゲートをGitHub Actions上で実行する。

- [x] Ubuntuでlint、typecheck、test、build、package、UI文言ポリシー検査を実行する。
- [x] macOS / Windowsでpytestとcompileallのplatform smokeを実行する。
- [x] CIは `MJPS_LLM_MODE=mock` を強制し、OpenAI APIキーや実API通信を不要にする。
- [x] package成果物はartifactとしてアップロードする。
- [x] READMEと `docs/process/ci.md` にCI運用を記載する。

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
| 2026-05-24 | `make lint` | Done | 再監査改修後、ruff: All checks passed |
| 2026-05-24 | `make typecheck` | Done | 再監査改修後、mypy: no issues found in 53 source files |
| 2026-05-24 | `make test` | Done | 再監査改修後、pytest: 14 passed |
| 2026-05-24 | `make build` | Done | 再監査改修後、compileall成功 |
| 2026-05-24 | `.venv/bin/python scripts/verify_ui_text.py` | Done | UI/resources走査で禁止UI文言なし |
| 2026-05-24 | `.venv/bin/python -m pip install --force-reinstall --no-cache-dir -e ".[dev]"` | Done | 既存venvのアーキテクチャ不一致を修復し、build依存を追加 |
| 2026-05-24 | `make lint` | Done | 販売品質再監査後、ruff: All checks passed |
| 2026-05-24 | `make typecheck` | Done | 販売品質再監査後、mypy: no issues found in 56 source files |
| 2026-05-24 | `make test` | Done | 販売品質再監査後、pytest: 16 passed |
| 2026-05-24 | `make build` | Done | 販売品質再監査後、compileall成功 |
| 2026-05-24 | `make package` | Done | sdist / wheel作成成功、`dist/` はgitignore対象 |
| 2026-05-24 | `.venv/bin/python scripts/verify_ui_text.py` | Done | UI/resources走査で禁止UI文言なし |
| 2026-05-24 | `git status --short --ignored` | Done | DB、ユーザー画像、APIキー、生成パッケージは未追跡またはignore対象 |
| 2026-05-24 | `rg -n "\\b[Vv]\\s*[0-9]+(\\.[0-9]+)?\\b|Midjourney\\s+[Vv]" src README.md docs plans \|\| true` | Done | 禁止表記ヒットなし |
| 2026-05-24 | `make lint` | Done | 機能別LLM設定追加後、ruff: All checks passed |
| 2026-05-24 | `make typecheck` | Done | 機能別LLM設定追加後、mypy: no issues found in 56 source files |
| 2026-05-24 | `make test` | Done | 機能別LLM設定追加後、pytest: 24 passed |
| 2026-05-24 | `make build` | Done | 機能別LLM設定追加後、compileall成功 |
| 2026-05-24 | `make package` | Done | 機能別LLM設定追加後、sdist / wheel作成成功、`dist/` はgitignore対象 |
| 2026-05-24 | `.venv/bin/python scripts/verify_ui_text.py` | Done | UI/resources走査で禁止UI文言なし |
| 2026-05-24 | `rg -n "\\b[Vv]\\s*[0-9]+(\\.[0-9]+)?\\b|Midjourney\\s+[Vv]" src README.md docs plans \|\| true` | Done | 禁止表記ヒットなし |
| 2026-05-24 | `git diff --check` | Done | whitespace errorなし |
| 2026-05-25 | `make lint` | Done | CI追加後、ruff: All checks passed |
| 2026-05-25 | `make typecheck` | Done | CI追加後、mypy: no issues found |
| 2026-05-25 | `make test` | Done | CI追加後、pytest: 24 passed |
| 2026-05-25 | `make build` | Done | CI追加後、compileall成功 |
| 2026-05-25 | `make package` | Done | CI追加後、sdist / wheel作成成功、`dist/` はgitignore対象 |
| 2026-05-25 | `.venv/bin/python scripts/verify_ui_text.py` | Done | UI/resources走査で禁止UI文言なし |
| 2026-05-25 | `rg -n "\\b[Vv]\\s*[0-9]+(\\.[0-9]+)?\\b|Midjourney\\s+[Vv]" src README.md docs plans \|\| true` | Done | 禁止表記ヒットなし |
| 2026-05-25 | `ruby -e 'require "yaml"; YAML.load_file(".github/workflows/ci.yml")'` | Done | GitHub Actions workflow YAMLの構文確認成功 |
| 2026-05-25 | `git diff --check` | Done | whitespace errorなし |
