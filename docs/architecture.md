# Architecture

## レイヤ構成

`MJ Prompt Studio` は `React UI -> Local API / Bridge -> Application -> Domain -> Infra / LLM adapter` の依存方向で構成する。

```text
React.js + TypeScript client
  -> typed API client
  -> localhost-only FastAPI bridge
  -> AppContext
  -> Application Services
  -> Domain / Infra / LLM
```

## React UI

責務:

- App Shell、タブ、左右/下部パネル、フォーム、確認ダイアログ、クリップボード、file picker / drag and dropを表示する。
- API clientを通じてApplication Serviceのユースケースを呼び出す。
- 表示中状態、入力中状態、pending patch、選択中variantなどUI状態だけを持つ。
- 永続化の正本をReact stateに置かない。

依存:

- `client/src/shared/api` のtyped API client。
- `client/src/shared/types` のAPI契約型。
- Python `infra`、SQLite、OpenAI SDKを直接呼ばない。

## Local API / Bridge

責務:

- `src/mj_prompt_studio/server/` にあるFastAPI bridgeとしてlocalhostにbindする。
- CORSはReact dev / preview originに限定する。
- `AppContext` をrequestから参照し、既存Application Serviceを呼ぶ。
- OpenAPI schemaを生成し、client型との同期を検証する。
- 画像uploadを検証し、safe asset endpointだけでpreviewを返す。

分岐条件:

- 開発時はVite dev serverから `/api` proxyで呼ぶ。
- build後のclient artifactが存在する場合はPython APIから静的配信できる。

## Application

責務:

- Composer、Reference、Matrix、Result Reviewなどのユースケースを束ねる。
- LLM出力をPatchまたはReviewとして受け取り、検証後にDomainへ適用する。
- RepositoryとAssetStoreを通じて保存する。
- Free Editor変換整形やExportなどの操作ポリシーを保持する。

依存:

- `domain`、`infra`、`llm`。
- ReactやHTTP固有型には依存しない。

## Domain

責務:

- `PromptDocument`、`PromptBlocks`、`PromptParameters`、`Ruleset`、`ValidationReport`。
- `ReferenceAsset` / `ResultImage` はローカル画像メタデータとAI分析結果を分けて保持する。
- Prompt Compiler、Validator、Matrix Generator。
- LLMやSQLiteに依存しない決定論的処理。

拡張ポイント:

- Ruleset JSONを増やすことでCapability Profileを差し替える。
- ValidatorはRulesetのParameterSpecとReferenceModeSpecに従う。

## Infra

責務:

- SQLite Repository、Asset Store、Settings、Secret Store、画像メタデータ抽出。
- APIキーは環境変数を優先し、利用可能な場合だけOS資格情報ストアへ保存する。
- 参照画像と生成結果画像はasset store配下へコピーし、DB recordと紐付ける。

制約:

- APIキー、ユーザー画像、DB、cache、log、exportはgit追跡対象にしない。
- asset preview endpointは既知IDだけを受け取り、任意pathを受け付けない。

## LLM

責務:

- Responses API adapter、MockLLM、Structured Outputs schema、Job Queue。
- Agent名とschemaを一致させ、schema検証後にApplicationへ返す。
- 機能別LLM設定はSQLite settingsへ保存し、Agent実行時にモデル、推論強度、語彙量として解決する。

分岐条件:

- `OPENAI_API_KEY` が端末環境変数にある場合は、起動時の既定を実API利用にする。
- `MJPS_LLM_MODE=mock` を明示した場合は、APIキーがあってもMockLLMを使う。
- それ以外はMockLLMで同じschemaの応答を返す。
- Privacy modeではResponses APIの保存を無効化し、会話ID継続を使わない。
