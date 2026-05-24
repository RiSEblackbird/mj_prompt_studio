# Architecture

## レイヤ構成

`MJ Prompt Studio` は `UI -> Application -> Domain -> Infra/LLM adapter` の依存方向で構成する。

## UI

責務:

- PySide6 Widget、MainWindow、Dock、Tabの表示。
- ユーザー操作をApplication Serviceへ渡す。
- Job Queueの状態、Validation、Patch候補を表示する。

依存:

- `application` と `domain` のDTO/dataclass。
- `infra` やOpenAI SDKを直接呼ばない。

## Application

責務:

- Composer、Reference、Matrix、Result Reviewなどのユースケースを束ねる。
- LLM出力をPatchまたはReviewとして受け取り、検証後にDomainへ適用する。
- RepositoryとAssetStoreを通じて保存する。
- Free Editor変換整形やExport option構築など、UIから切り出せる操作ポリシーを保持する。

依存:

- `domain`、`infra`、`llm`。
- UI固有型には依存しない。

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

- SQLite Repository、Asset Store、Settings、Secret Store。
- ローカルDB、画像コピー、画像メタデータ抽出、環境変数/資格情報境界。
- APIキーは環境変数を優先し、利用可能な場合だけOS資格情報ストアへ保存する。

制約:

- APIキー、ユーザー画像、DB、cache、log、exportはgit追跡対象にしない。

## LLM

責務:

- Responses API adapter、MockLLM、Structured Outputs schema、Job Queue。
- Agent名とschemaを一致させ、schema検証後にApplicationへ返す。

分岐条件:

- `MJPS_LLM_MODE=real` かつAPIキーがある場合のみ実APIを使う。
- それ以外はMockLLMで同じschemaの応答を返す。
