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

起動後にSettingsタブでセッション内APIキーを入力して接続テストすることもできます。保存時は利用可能なOS資格情報ストアを使い、使えない場合はセッション内適用に限定します。

## 5. 基本フロー

1. Composerで日本語Briefを入力する。
2. `AIで構成案を作る` を押す。
3. Prompt Blocksを編集する。
4. 各入力欄の `AI補完`、`候補`、`専門語化`、`短縮`、`説明` を必要に応じて使う。適用前にPatch差分を確認する。
5. `Compile` でCompiled Promptを生成する。Prompt Compiler AgentのレビューはJobとして実行される。
6. 必要ならParameter Advisorで目的別提案を作り、確認後に適用する。
7. 生成サービスへ手動コピーする。
8. 参照画像をReference Libraryへ取り込み、プレビュー、メタデータ、AI分析、抽出語彙を確認する。
9. 結果画像をResult Reviewへ手動取り込みする。
10. AI ReviewとNext Prompt Candidatesを確認する。
11. 改善候補はComposerへPatchとして戻し、差分確認後に適用する。

## 6. エクスポートと配布物

- ToolbarのExportからPrompt only、Markdown record、JSON snapshot、CSV/Markdown matrix variantsを保存できます。
- 配布用のPythonパッケージは `make package` で `dist/` に作成できます。
- 作業中の変更はToolbarのUndo/Redoで戻せます。
