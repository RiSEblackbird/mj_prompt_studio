# Quick Start

## 1. インストール

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## 2. 起動

```bash
make run
```

## 3. APIキーなしで試す

既定では `MJPS_LLM_MODE=mock` と同等に動作する。AI Brief、Prompt Doctor、Reference Analysis、Matrix Planning、Result Reviewはモック応答で確認できる。

## 4. 実APIを使う

```bash
export OPENAI_API_KEY="..."
export MJPS_LLM_MODE=real
make run
```

起動後にSettingsタブでセッション内APIキーを入力して接続テストすることもできます。入力したキーは永続保存しません。

## 5. 基本フロー

1. Composerで日本語Briefを入力する。
2. `AIで構成案を作る` を押す。
3. Prompt Blocksを編集する。
4. `Compile` でCompiled Promptを生成する。
5. 生成サービスへ手動コピーする。
6. 結果画像をResult Reviewへ手動取り込みする。
7. AI ReviewとNext Prompt Candidatesを確認する。
8. 改善候補はComposerへPatchとして戻し、差分確認後に適用する。
