# LLM Agents

## 共通方針

- すべてのAgent出力は `response_schemas.py` のJSON schemaで検証する。
- ローカルではPydantic modelでも必須fieldと主要型を検証する。
- UIはLLM結果を直接保存せず、Application ServiceがPatch、Suggestion、Reviewとして扱う。
- Patchは適用前に差分確認を必須にする。
- APIキー未設定時はMockLLMが同じschemaで応答する。
- LLM Jobは `queued`、`running`、`succeeded`、`failed`、`cancelled` の状態を持ち、UIからキャンセルと再実行を操作できる。
- SettingsでAgentごとにモデル、推論強度、語彙量を保存できる。既定は `gpt-5.5`、`medium`、`standard`。
- ログやJob payloadにはAPIキー、Token、Cookieを含めない。
- React UIはAgentを直接呼ばず、`/api/agents/*` または機能別endpointからJobを作成する。
- Job結果の永続化やPromptDocument更新はPython Application Service / Repositoryを通す。
- 実API経路もMockLLMと同じschemaを使う。Structured Outputs向けのJSON schemaは、objectごとに `additionalProperties: false` と必須fieldを明示する。

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

## Job API

主なendpoint:

- `/api/agents/intent-intake`
- `/api/agents/vocabulary`
- `/api/agents/compile-review`
- `/api/agents/prompt-doctor`
- `/api/agents/parameter-advisor`
- `/api/agents/reference-analyzer`
- `/api/agents/matrix-planner`
- `/api/agents/result-review`
- `/api/agents/final-audit`
- `/api/jobs`
- `/api/jobs/{job_id}`
- `/api/jobs/{job_id}/cancel`
- `/api/jobs/{job_id}/retry`
- `/api/jobs/stream`

SSEが使えない環境でもReact clientは1秒pollingでJob状態を更新する。

## 実API手動検証

CIではOpenAI実APIを呼ばない。納品前またはリリース前に、APIキーを設定した環境で次を確認する。

1. `OPENAI_API_KEY` またはSettingsのSession API keyを設定する。
2. `make run` でローカルAPIとReact UIを起動する。
3. `Settings`で接続テストを実行し、成功状態になることを確認する。
4. `Composer`で日本語briefを入力し、`AI Brief から構造化`を実行する。
5. Jobsで `IntentIntakeAgent` が `succeeded` になり、Prompt BlocksとCompiled Promptが更新されることを確認する。
6. Privacy modeを有効にした状態で同じ操作を行い、Responses API requestがresponse storageを使わない経路で動くことを確認する。

2026-05-25時点の代表確認では、環境変数のAPIキーを使い、接続テストと `IntentIntakeAgent` のschema-valid実行が成功している。

参考にした公式ドキュメント:

- [Responses API Reference](https://platform.openai.com/docs/api-reference/responses)
- [Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
- [gpt-5.5](https://developers.openai.com/api/docs/models/gpt-5.5)
- [gpt-5.4-mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini)
- [gpt-5.4-nano](https://developers.openai.com/api/docs/models/gpt-5.4-nano)
