# CI

GitHub Actionsの `CI` ワークフローは、Pull Requestと `main`、`master`、`codex/**` へのpushで実行する。

## Quality and package

Ubuntu上で以下を実行する。

- `make lint`
- `make typecheck`
- `make test`
- `make build`
- `make package`
- `python scripts/verify_ui_text.py`
- ユーザー向け文書とUI文字列への禁止バージョン表記混入チェック

LLMは `MJPS_LLM_MODE=mock` 固定で実行し、CIではOpenAI APIキーや外部API通信を必要としない。

## Platform smoke

macOSとWindowsで以下を実行する。

- `python -m pytest`
- `python -m compileall -q src`

PySide6のGUI smoke testは `QT_QPA_PLATFORM=offscreen` で実行する。
