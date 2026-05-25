# React + TypeScript 移行計画

## 目的

PySide6 クライアントを production path から除去し、React.js + TypeScript client と localhost Python API/bridge で `MJ Prompt Studio` の既存主要機能を実運用可能な形へ移行する。

## 非目標

- 既存 Domain / Application / Infra / LLM を TypeScript へ再実装しない。
- 画像生成サービス本体、Discord、Cookie、Token、非公式 API を自動操作しない。
- Tauri desktop shell は今回の必須完成形にしない。代替仕様として `make run` で localhost API と React UI を起動するローカル Web アプリへ製品仕様を更新する。
- 実 OpenAI API キーが必要な手動検証を CI に含めない。

## 対象範囲

- `src/mj_prompt_studio/server/`: FastAPI ベースの localhost API / bridge。
- `client/`: Vite React TypeScript client、typed API client、Vitest、Playwright。
- `src/mj_prompt_studio/app/app_context.py`: UI 非依存 composition root として継続利用。
- `src/mj_prompt_studio/application/`, `domain/`, `infra/`, `llm/`: API 経由で再利用し、必要な UI 依存除去のみ行う。
- `README.md` と関連 `docs/`: React + local API 仕様へ更新。
- PySide6 production code、QSS、PySide6 専用テスト、PySide6 依存の削除。

## 採用アーキテクチャ

完成形は local web product 化を採用する。

```text
React.js + TypeScript client
  -> typed API client
  -> localhost-only FastAPI bridge
  -> AppContext
  -> Application Services
  -> Domain / Infra / LLM
```

理由:

- 既存 Python 側は Application Service まで UI と分離済みで再利用できる。
- 即納品の観点では Tauri 同梱より、`make run` で API と Vite preview を起動する導線の方が検証と障害切り分けが明確。
- デスクトップ shell 採用は後続タスクとして追加可能で、今回のユーザー価値は React UI + local persistence + asset store + LLM job の parity 達成にある。

## 運用是正記録

- 2026-05-25: AGENTS.md の「作業ブランチを作成して作業」「コミットしながら進める」ルールを再確認した。初期実装を `main` 上の未コミット差分として進めていたため、以後の作業前に差分を保持したまま `codex/react-typescript-migration` ブランチへ移動した。
- 2026-05-25: 実 API 検証で、環境変数の API key が composition root に反映されない問題と、Responses API 入力 item / Structured Outputs schema が実 API 境界で不十分な問題を確認した。修正は LLM schema / client adapter 境界として扱い、mock test、contract test、実 API representative check、docs を同じ変更内で更新する。
- 以後は各検証ゲート通過後に plan を更新し、日本語コミットを作成してから次の大きな作業へ進む。

## 移行前棚卸し

### PySide6 依存抽出

実行コマンド:

```bash
rg "PySide6|QApplication|QMainWindow|QWidget|QDialog|QFileDialog|QMessageBox|QClipboard|QPixmap|Signal|Slot|QTimer|QDockWidget|QTabWidget" src tests
```

分類:

- 起動点:
  - `src/mj_prompt_studio/app/main.py`: `QApplication` 起動。
- app shell / layout:
  - `src/mj_prompt_studio/app/main_window.py`: `QMainWindow`, `QDockWidget`, `QTabWidget`, toolbar, left/right/bottom dock。
- form input:
  - `src/mj_prompt_studio/ui/widgets/composer_widget.py`
  - `src/mj_prompt_studio/ui/widgets/free_editor_widget.py`
  - `src/mj_prompt_studio/ui/widgets/matrix_lab_widget.py`
  - `src/mj_prompt_studio/ui/widgets/parameter_inspector.py`
  - `src/mj_prompt_studio/ui/widgets/settings_widget.py`
- file dialog / drag and drop:
  - `src/mj_prompt_studio/app/main_window.py`: export save dialog。
  - `src/mj_prompt_studio/ui/widgets/reference_library_widget.py`: file picker, drag/drop。
  - `src/mj_prompt_studio/ui/widgets/result_review_widget.py`: file picker。
- clipboard:
  - `src/mj_prompt_studio/app/main_window.py`: prompt, markdown record, matrix CSV/Markdown, selected/all variant copy。
- image preview:
  - `src/mj_prompt_studio/ui/widgets/reference_library_widget.py`: `QPixmap` preview。
  - `src/mj_prompt_studio/ui/widgets/result_review_widget.py`: `QPixmap` preview。
  - `src/mj_prompt_studio/infra/image_probe.py`: `QImage` metadata probe。UI 非依存へ置換必須。
- modal confirmation:
  - `src/mj_prompt_studio/app/main_window.py`: patch apply、parameter apply、reference delete、empty input。
- timer / debounce:
  - `src/mj_prompt_studio/ui/widgets/composer_widget.py`: 1000ms auto suggestion debounce。
  - `src/mj_prompt_studio/ui/widgets/jobs_panel.py`: job refresh timer。
- background job polling:
  - `src/mj_prompt_studio/ui/widgets/jobs_panel.py`: `QTimer`。
  - `src/mj_prompt_studio/app/main_window.py`: `JobBridge` signal callback。
- styling / QSS:
  - `src/mj_prompt_studio/ui/themes/dark.qss`
  - `src/mj_prompt_studio/ui/themes/light.qss`
- tests only:
  - `tests/test_reference_metadata.py`: PySide6 `QImage` fixture helper。
  - `tests/test_ui_smoke.py`: PySide6 widget smoke。

### 現行ワークフロー checklist

- [x] 新規プロジェクト作成: `/api/projects` + React toolbar。
- [x] プロジェクト選択/読込: `/api/projects` / `/api/projects/{project_id}/open` + Project Explorer。
- [x] PromptDocument 保存: `/api/prompt-documents/{document_id}/blocks` と `compile`。
- [x] Undo / Redo と revision 保存: API state stack + revision endpoint。
- [x] AI Brief から Prompt Blocks 生成: `/api/agents/intent-intake` Job。
- [x] Prompt Blocks 手動編集: React Composer 全 field。
- [x] 1 秒 debounce の自動提案: React Composer debounce + stale source discard。
- [x] field assist: `AI補完`, `候補`, `専門語化`, `短縮`, `説明`: VocabularyAgent Job + patch確認。
- [x] Compile: deterministic compile + validation + revision。
- [x] Prompt copy: Clipboard API + fallback dialog。
- [x] Parameter Advisor 提案と確認付き適用: Job + confirmation dialog。
- [x] Prompt Doctor 実行、Patch 一覧、確認付き適用: Job + confirmation dialog。
- [x] Free Editor の 6 種変換: React Free Editor + Job。
- [x] Reference image の file picker 取り込み: upload endpoint + AssetStore。
- [x] Reference image の drag & drop 取り込み: React drop zone + upload endpoint。
- [x] Reference preview、palette、metadata 表示: safe asset endpoint + metadata。
- [x] Reference AI analysis: ReferenceAnalyzerAgent Job。
- [x] Reference search/filter/tags/delete: React UI + API + asset delete。
- [x] Reference vocabulary を Composer patch として戻す: patch confirmation dialog。
- [x] Matrix AI plan: MatrixPlannerAgent Job。
- [x] Matrix variant 生成: MatrixGenerator + repository 保存。
- [x] Matrix selected/all copy: Clipboard API + fallback dialog。
- [x] Matrix CSV / Markdown export: API export + copy/download。
- [x] Result image 取り込み: upload endpoint + AssetStore。
- [x] Result preview、source prompt、parameters snapshot 表示: safe asset endpoint + metadata。
- [x] Result AI review: ResultReviewAgent Job。
- [x] Result comparison: compare endpoint。
- [x] Next Prompt Candidate を Composer patch として戻す: patch confirmation dialog。
- [x] Final Audit: FinalAuditorAgent Job。
- [x] Export: prompt only、Markdown record、JSON snapshot、Matrix CSV/Markdown: API export。
- [x] Jobs list、refresh、cancel、retry、failed 表示: Jobs panel + polling/SSE fallback。
- [x] Settings: API key session apply、keyring 保存、Privacy mode、feature profile 保存、connection test: React Settings + API。

### データ契約一覧

React TypeScript 型へ反映する Python モデル:

- `PromptDocument`
- `PromptBlocks`
- `PromptParameters`
- `PromptReferences`
- `LLMContext`
- `ValidationIssue`
- `ValidationReport`
- `PromptPatch`
- `ReferenceAsset`
- `ReferenceAnalysis`
- `ImageMetadata`
- `ResultImage`
- `ResultReview`
- `MatrixAxis`
- `MatrixPlan`
- `MatrixVariant`
- `LLMJob`
- `LLMFeatureProfile`
- `RuntimeSettings` の UI 公開分
- `GenerationRuleset`, `ParameterSpec`, `ReferenceModeSpec` の UI 公開分

同期方針:

- Python API の OpenAPI schema を `client/src/shared/types/openapi.json` として生成する。
- TypeScript 型は `client/src/shared/types/api.ts` に集約し、OpenAPI 由来の契約と同期するテストを置く。
- 初期実装では手書き型を使うが、schema 生成差分を `tests/test_api_contract.py` で固定する。

## 外部公式ドキュメント確認

- React TypeScript: `https://react.dev/learn/typescript` を確認。`.tsx`、`@types/react`、strict な state 型を採用。
- Vite: `https://vite.dev/guide/` を確認。React TypeScript scaffold と build script 方針に反映。
- Vitest: `https://vitest.dev/guide/` を確認。client unit test に採用。
- Playwright: `https://playwright.dev/docs/intro` を確認。E2E に採用。
- Tauri: 公式サイトを確認。今回は非採用、代替の local web product 化を docs に明記。
- FastAPI file upload / OpenAPI: `https://fastapi.tiangolo.com/tutorial/request-files/` を確認。`UploadFile` と multipart upload を採用。
- OpenAI Responses API: `https://platform.openai.com/docs/api-reference/responses` を確認。既存 `OpenAIResponsesClient` の Responses API 経路を維持。
- OpenAI Structured Outputs: `https://developers.openai.com/api/docs/guides/structured-outputs` を確認。schema validation と structured output 契約を維持。

## マイルストーン

- [x] M0 Task: 棚卸しと plan 作成。
- [x] M1 Task: Python API / bridge を実装し、AppContext と既存 Application Service を HTTP から呼べるようにする。
- [x] M2 Task: Vite React TypeScript client と typed API client を追加し、workspace を実 API から表示する。
- [x] M3 Task: Composer / Parameter / Prompt Doctor / Jobs を React UI へ移植する。
- [x] M4 Task: Free Editor / Reference Library を React UI へ移植する。
- [x] M5 Task: Matrix Lab / Result Review / Export を React UI へ移植する。
- [x] M6 Task: local web product として `make run` / package 統合と docs を整える。
- [x] M7 Task: PySide6 production path を完全除去し、検証と E2E parity を通す。

## 受け入れ条件

## Goal 完了条件

- [x] React + TypeScript client が local Python API / bridge 経由で既存 Application Service / Domain / Infra / LLM を利用している。
- [x] PySide6 起動点、Widget、QSS、依存が production path から除去されている。
- [x] README / docs / CI / Makefile が local web product 仕様に更新されている。
- [x] Python / React / E2E / package / UI文言 / 実API代表確認が通っている。

PR 作成と push は最終手順で実施し、結果は最終報告へ記載する。

- [x] README の手順だけで local API と React UI が起動できる。
- [x] 現行 README / docs の主要機能が React UI で使用できる。
- [x] React UI が Python Application Service / SQLite / AssetStore / SecretStore / LLMOrchestrator / JobQueue に接続されている。
- [x] production code に PySide6 import が残っていない。
- [x] production code に仮実装、固定成功レスポンス、未接続ボタン、placeholder UI が残っていない。
- [x] OpenAI API key ありの real path と、API key なしの mock path の両方が仕様どおり動く。
- [x] Privacy mode が real API request の `store` と `previous_response_id` に反映される。
- [x] 画像 upload、asset 保存、preview、削除、Result Review が実ファイルで動く。
- [x] SQLite persistence と再起動後復元が動く。
- [x] Job cancel / retry / failed 表示が動く。
- [x] Export が download または file response として取得できる。
- [x] Python 検証、React 検証、E2E、package が通る。
- [x] README と関連 docs が移行後の実装に一致している。

## 検証コマンド

- `make lint`
- `make typecheck`
- `make test`
- `make build`
- `make package`
- `make client-install`
- `make client-lint`
- `make client-typecheck`
- `make client-test`
- `make client-build`
- `make e2e`
- `make run` 手動起動確認

## 既知 blocker

- なし。
- Tauri 同梱は今回非採用。顧客向け仕様は local web product として文書化済み。

## feature flag / rollback

- React 移行は cohesive commit とし、通常の git revert で PySide6 版へ戻せる単位にまとめる。
- API は localhost-only で bind し、CORS origin を dev / packaged client に限定する。

## 検証記録

| 日時 | コマンド | 結果 | メモ |
|---|---|---|---|
| 2026-05-25 | `make lint` | Pass | `All checks passed!` |
| 2026-05-25 | `make typecheck` | Pass | `Success: no issues found in 56 source files` |
| 2026-05-25 | `make test` | Pass | `24 passed in 0.69s` |
| 2026-05-25 | `make build` | Pass | `compileall` 成功 |
| 2026-05-25 | `make package` | Pass | sdist / wheel 生成成功 |
| 2026-05-25 | `make generate-openapi` | Pass | `client/src/shared/types/openapi.json` を更新 |
| 2026-05-25 | `make lint` | Pass | `All checks passed!` |
| 2026-05-25 | `make typecheck` | Pass | `Success: no issues found in 49 source files` |
| 2026-05-25 | `make test` | Pass | `28 passed in 0.54s` |
| 2026-05-25 | `make build` | Pass | `compileall` 成功 |
| 2026-05-25 | `make client-lint` | Pass | ESLint 成功 |
| 2026-05-25 | `make client-typecheck` | Pass | TypeScript strict build 成功 |
| 2026-05-25 | `make client-test` | Pass | `2 passed (2)`, `3 passed (3)` |
| 2026-05-25 | `make client-build` | Pass | Vite production build 成功 |
| 2026-05-25 | `make e2e` | Pass | Playwright Chromium `core local workflow parity` 成功 |
| 2026-05-25 | `make package` | Pass | sdist / wheel 生成成功 |
| 2026-05-25 | `PYTHONPATH=src .venv/bin/python scripts/verify_ui_text.py` | Pass | UI / docs 文言ポリシー違反なし |
| 2026-05-25 | `rg "PySide6|QApplication|QMainWindow|QWidget|QDialog|QFileDialog|QMessageBox|QPixmap|QTimer|Signal" src tests` | Pass | production / tests に一致なし |
| 2026-05-25 | 実API代表確認 | Pass | API key 環境で connection test と `IntentIntakeAgent` schema-valid 実行に成功 |
