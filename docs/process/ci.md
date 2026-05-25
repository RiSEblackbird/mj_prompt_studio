# CI

GitHub Actionsの `CI` ワークフローは、Pull Requestと `main`、`master`、`codex/**` へのpushで実行する。

## Quality and package

Ubuntu上で以下を実行する。

- `make lint`
- `make typecheck`
- `make test`
- `make build`
- `make client-install`
- `make client-lint`
- `make client-typecheck`
- `make client-test`
- `make client-build`
- `make e2e`
- `make package`
- `make generate-openapi`
- `python scripts/verify_ui_text.py`
- ユーザー向け文書とUI文字列への禁止バージョン表記混入チェック

LLMは `MJPS_LLM_MODE=mock` 固定で実行し、CIではOpenAI APIキーや外部API通信を必要としない。

## Platform smoke

macOSとWindowsで以下を実行する。

- `python -m pytest`
- `python -m compileall -q src`
- `cd client && npm run build`
- 必要に応じて `cd client && npx playwright install chromium` の後にE2Eを実行する。

UIはReact client + localhost Python APIで検証する。PySide6 GUI smoke testは廃止済み。
