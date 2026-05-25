# UI Spec

## 全体構成

- Header / Toolbar: 新規プロジェクト、Undo/Redo、Export、保存状態。
- Left Panel: Project Explorer、Quick Actions。
- Main Tabs: Composer、Free Editor、Matrix Lab、Reference Library、Result Review、Settings。
- Right Panel: AI Inspector、Parameter Advisor、Prompt Doctor。
- Bottom Panel: Status、Jobs。

Dock実装ではなくReact layoutで構成する。情報配置は旧クライアントの作業順序を維持する。

## Composer

主要操作:

- 日本語のAI Brief入力。
- `AI Brief から構造化` でIntent Intake AgentをJob Queue経由で実行。
- Prompt Blocks全項目を手動編集する。
- 各Blockに `AI補完`、`候補`、`専門語化`、`短縮`、`説明` を表示する。
- 1000ms debounceで自動提案をJob Queueへ流し、古い入力に対する完了結果は破棄する。
- `Compile` で決定論的Prompt CompilerとValidatorを実行し、Prompt Compiler Agentのレビューを非同期表示する。
- `Compiled Prompt` はClipboard APIでコピーし、失敗時は手動コピー用textareaを出す。
- Undo/Redoで保存済みPromptDocument状態を戻す。
- AI Patchは候補として表示し、適用前にreason、field_path、old_value、new_value、confidenceを確認する。

空状態:

- 初回起動時はサンプルプロジェクトとPromptDocumentを作る。

エラー状態:

- LLM Job失敗時は下部Jobsとstatusに安全なエラーを表示する。

## Free Editor

主要操作:

- 日本語入力と英語promptを受け付ける。
- 6種変換をVocabularyAgent jobとして実行する。
- 変換結果とdetailを表示する。

## Reference Library

主要操作:

- 画像ファイルをfile pickerまたはdrag & dropでAPI upload endpointへ送る。
- 取り込み時にAssetStoreへ保存し、画像サイズ、形式、ファイルサイズ、簡易カラーパレットをローカル抽出する。
- safe asset URLでpreviewを表示し、OS local pathはDOMへ出さない。
- AI分析で照明、色、構図、質感、推奨モード、語彙を保存する。
- タイトル、タグ、抽出語彙で検索する。
- タグを保存し、削除時は確認ダイアログを表示する。
- 抽出語彙をComposerへPatchとして戻す。

## Matrix Lab

主要操作:

- 実験目的からAIが軸と固定条件を提案する。
- 決定論的Generatorがvariantを展開しRepositoryへ保存する。
- 選択Variantコピー、一括コピー、CSV/Markdown download/copyができる。

## Result Review

主要操作:

- 生成結果画像をfile pickerでAPI upload endpointへ送る。
- Source Prompt、parameters snapshot、previewへ紐付ける。
- AI Review、複数画像比較、Next Prompt Candidate、Final Auditを表示する。
- Next Prompt CandidateはComposerへPatchとして戻し、適用前に確認する。

## Settings

表示:

- セッション内API key適用。
- OS資格情報ストアへのAPI key保存。保存不可環境ではセッション内適用に留める。
- Privacy mode / normal response storage。
- 機能別LLM設定: モデル、推論強度、語彙量。
- Ruleset display_name。
- connection test。

UIではRulesetの内部IDと特定のMidjourneyモデルバージョン番号を表示しない。
