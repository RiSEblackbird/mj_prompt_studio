# MJ Prompt Studio ユーザーマニュアル

MJ Prompt Studioは、画像生成に使うプロンプトを考え、整え、比較し、結果を見直すための制作支援アプリです。画像生成サービスを自動操作するアプリではありません。最終プロンプトは自分でコピーし、生成結果の画像も自分で取り込みます。

## 起動と画面構成

`make run` でlocalhost APIとReact clientを起動し、ブラウザで `http://127.0.0.1:5173` を開きます。

画面は次の領域に分かれています。

- Header: 新規プロジェクト、Undo/Redo、Export。
- Left Panel: プロジェクト一覧、Quick Actions。
- Main Tabs: `Composer`、`Free Editor`、`Matrix Lab`、`Reference Library`、`Result Review`、`Settings`。
- Right Panel: AI Inspector、Parameter Advisor、Prompt Doctor。
- Bottom Panel: 保存状態とJobs。

## AI接続

AI支援を使う場合は、起動前に環境変数 `OPENAI_API_KEY` にAPIキーを入れておくと自動で読み取ります。

```bash
export OPENAI_API_KEY="..."
```

起動後に設定する場合は `Settings` を開き、`API Key` に入力して `Session` を押します。OS資格情報ストアへ保存する場合は `Keyring` を押します。保存できない環境では、その起動中だけ有効になります。

APIキーがない場合はMockLLMで同じ画面フローを試せます。実APIの接続確認は `Test` で実行します。

## Privacy Mode

`Settings` の `Privacy mode` を有効にすると、Responses APIの保存を無効化し、会話ID継続を使いません。画像解析や結果レビューを実行する場合、対象画像と必要なメタデータはAIへ送られます。

## プロジェクト

- `New`: 新しいプロジェクトとPromptDocumentを作る。
- Project Explorer: 既存プロジェクトを開く。
- `Undo` / `Redo`: 保存済みPromptDocument状態を戻す。
- `Export`: Markdown recordなどを出力する。

保存と読み込みの正本はSQLiteです。React stateは表示中状態に限定されます。

## Composer

1. `AI Brief`に日本語で制作意図を書く。
2. `AI Brief から構造化`を押す。
3. Prompt Blocksを確認し、必要な欄を直す。
4. 各Blockの `AI補完`、`候補`、`専門語化`、`短縮`、`説明` で語彙補助を使う。
5. `Compile`を押す。
6. `Compiled Prompt`を確認し、コピーアイコンでコピーする。

AIが返すPatchは、reason、field_path、old_value、new_value、confidenceを確認してから適用します。

## Parameter Advisor

右側のParameter AdvisorはRulesetで表示可能なパラメータからフォームを生成します。手動変更した値は次のCompileに使われます。AI提案を使う場合はAI adviceボタンを押し、提案内容と理由を確認してから適用します。

## Prompt Doctor

右側のPrompt DoctorはValidatorのissueとAI修正候補を表示します。Run Prompt Doctorを押すとJobが作成され、完了後にPatch候補が表示されます。Patchは確認ダイアログを通して適用します。

## Free Editor

`Free Editor`では日本語メモや既存promptを6種の変換で整えます。変換はVocabularyAgent jobとして実行され、結果欄に反映されます。

## Reference Library

1. `Add` またはdrag and dropで画像を取り込む。
2. プレビュー、画像サイズ、形式、カラーパレットを確認する。
3. 分析アイコンでReferenceAnalyzerAgentを実行する。
4. 抽出語彙を選び、ComposerへのPatchとして戻す。
5. タグを編集して保存する。
6. 不要な素材は削除アイコンから確認後に削除する。

React UIにはOS local pathを表示しません。previewはsafe asset endpointから返されます。

## Matrix Lab

1. Objectiveに比較したい目的を書く。
2. `AI Plan`で実験計画を作る。
3. `Generate`でvariantを展開する。
4. selected/all copy、CSV、Markdownを使って生成サービスへ手動投入する。

variant生成は決定論的Generatorで行われ、Repositoryへ保存されます。

## Result Review

1. 生成サービス側で作った画像をローカルに保存する。
2. `Result Review`の`Import`で画像を取り込む。
3. Source Promptとparameters snapshotを確認する。
4. `AI Review`でスコア、良い点、課題、Next Prompt Candidateを保存する。
5. `Next Prompt`を使う場合は確認ダイアログで差分を確認して適用する。
6. `Compare`で複数レビューを比較する。
7. `Final Audit`でコピー前の最終確認を行う。

## Jobs

AI処理はJob Queueで実行され、下部に状態が表示されます。

- `queued`: 順番待ち。
- `running`: 処理中。
- `succeeded`: 完了。
- `failed`: 失敗。
- `cancelled`: キャンセル済み。

実行中Jobはキャンセルできます。失敗したJobは再実行できます。

## エクスポート

利用できる主な形式:

- Prompt only
- Markdown record
- JSON snapshot
- Matrix CSV
- Matrix Markdown

ブラウザのClipboard APIが使えない場合は、手動コピー用のtextareaが表示されます。
