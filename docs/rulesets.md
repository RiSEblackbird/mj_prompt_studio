# Rulesets

## 目的

Rulesetは画像生成サービス仕様差分をUIから分離するCapability Profileである。UIは `display_name` のみを表示し、内部IDは通常表示しない。

## 構造

`resources/rulesets/standard.json` は以下を持つ。

- `ruleset_id`: 内部識別子。
- `display_name`: ユーザー向け表示名。
- `ui_expose_identifier`: UIに内部IDを出すかどうか。
- `capabilities`: 参照モードやパラメータの機能可否。
- `parameters`: flag、値域、型、UI表示可否、export可否。
- `reference_modes`: Image Reference、Style Reference、Moodboard、Personalization Profile。
- `compatibility_rules`: ValidatorやPrompt Doctorへ渡す汎用ルール。
- `output_order`: Prompt Compilerのパラメータ出力順。

## 追加方法

1. `resources/rulesets/` にJSONを追加する。
2. `display_name` は汎用名にする。
3. UIに内部IDや特定モデルバージョン番号を出さない。
4. compiler、validator、UI表示、禁止文言テストを更新する。

## 表示ルール

使用してよい表示:

- `Standard Ruleset`
- `Current Ruleset`
- `Prompt Compatibility`
- `Parameter Rules`
- `Reference Modes`

使用しない表示:

- 特定のMidjourneyモデルバージョン番号。
- サービス状態を誤認させる名前。
