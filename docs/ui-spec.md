# UI Spec

## 全体構成

- 左ペイン: Project Explorer、Prompt History、Quick Actions。
- 中央タブ: Composer、Free Editor、Matrix Lab、Reference Library、Result Review、Settings。
- 右ペイン: AI Inspector、Parameter Advisor、Prompt Doctor。
- 下部: Status、Jobs、Validation。

## Composer

主要操作:

- 日本語のAI Brief入力。
- `AIで構成案を作る` でIntent Intake AgentをJob Queue経由で実行。
- Prompt Blocksを手動編集。
- 各Blockに `AI補完`、`候補`、`専門語化`、`短縮`、`説明` を表示。
- 入力停止後に軽いAI提案をJob Queueへ流し、古い自動提案は破棄する。
- `Compile` で決定論的Prompt CompilerとValidatorを実行し、Prompt Compiler Agentのレビューを非同期表示する。
- `コピー` でCompiled Promptをクリップボードへ入れる。
- ToolbarのUndo/Redoで保存済みPromptDocument状態を戻す。
- AI Patchは候補として表示し、適用前に対象、変更前、変更後、理由を確認する。

空状態:

- 初回起動時はサンプルプロジェクトと空のPromptDocumentを作る。

エラー状態:

- Brief未入力時はダイアログで入力を促す。
- LLM Job失敗時は下部Jobsに安全なエラーを表示する。

## Reference Library

主要操作:

- 画像ファイルを手動で選択してasset storeへコピー。
- 画像ファイルをドラッグ&ドロップして取り込む。
- 取り込み時に画像サイズ、形式、ファイルサイズ、簡易カラーパレットをローカル抽出する。
- 参照素材のプレビューとReference Modeフィルターを表示する。
- AI分析で照明、色、構図、質感、推奨モード、語彙を保存。
- タイトル、タグ、抽出語彙で検索する。
- タグを保存し、削除時は確認ダイアログを表示する。
- 抽出語彙をComposerへPatchとして戻す。
- 自動アップロードや生成サービス操作は行わない。

## Matrix Lab

主要操作:

- 実験目的からAIが軸と固定条件を提案。
- 決定論的Generatorがvariantを展開。
- 選択Variantコピー、一括コピー、CSV/Markdownコピーができる。

## Result Review

主要操作:

- ユーザーが生成結果画像を手動取り込み。
- 画像プレビュー、元プロンプト、parameters snapshotへ紐付け。
- AI Review、複数画像比較の基礎、Next Prompt Candidates、Final Auditを表示。
- Next Prompt CandidateはComposerへPatchとして戻し、適用前に確認する。

## Settings

表示:

- AIモデル設定。
- Current Rulesetのdisplay_name。
- Response Storage / Privacy mode。
- セッション内APIキー適用。
- 利用可能なOS資格情報ストアへのAPIキー保存。
- 接続テスト。

UIではRulesetの内部IDを表示しない。
