# LLM Agents

## 共通方針

- すべてのAgent出力は `response_schemas.py` のJSON schemaで検証する。
- ローカルではPydantic modelでも必須fieldと主要型を検証する。
- UIはLLM結果を直接保存せず、Application ServiceがPatch、Suggestion、Reviewとして扱う。
- Patchは適用前に差分確認を必須にする。
- APIキー未設定時はMockLLMが同じschemaで応答する。
- LLM Jobは `queued`、`running`、`succeeded`、`failed`、`cancelled` の状態を持ち、UIからキャンセルと再実行を操作できる。
- ログやJob payloadにはAPIキー、Token、Cookieを含めない。

## Agent一覧

| Agent | 入力 | 出力 | 失敗時挙動 |
|---|---|---|---|
| IntentIntakeAgent | 日本語brief、Ruleset表示名 | intent、subject、prompt_blocks、suggested_parameters、missing_decisions | Job failedとして表示 |
| VocabularyAgent | 曖昧語、短文 | suggestions、PromptPatch案 | Patchは確認対象 |
| PromptCompilerAgent | compiled prompt、document snapshot | compiled_prompt、rationale | 決定論的compiler結果を保持 |
| PromptDoctorAgent | compiled prompt、validation report | summary、issues、patches、next_actions | Validator結果だけ表示 |
| ParameterAdvisorAgent | objective、Ruleset | profile_name、parameters、rationale | 既存parametersを保持 |
| ReferenceAnalyzerAgent | reference metadata、画像 | summary、colors、lighting、composition、mode、vocabulary | 手動取り込み素材は保持 |
| MatrixPlannerAgent | experiment objective | axes、fixed_conditions、evaluation_points | 手動軸入力に戻せる |
| ResultReviewAgent | result image、prompt snapshot | scores、strengths、issues、next_prompt_candidates | 手動レビューだけ保存 |
| FinalAuditorAgent | prompt、validation | approved、summary、warnings、patches | コピー前警告として表示 |

## OpenAI Responses API

実APIモードではOpenAI Python SDKのResponses APIを使い、`text.format` にJSON schemaを渡す。`Privacy mode` の場合は `store=false` とし、`previous_response_id` を送らない。

参考にした公式ドキュメント:

- [Responses API Reference](https://platform.openai.com/docs/api-reference/responses)
- [Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
