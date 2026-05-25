# 添付スクリーンショット準拠のUIビジュアル調整

## 目的

添付された6枚のスクリーンショットを基準に、MJ Prompt Studio のReactクライアントの色、余白、境界線、パネル構成、ボタン、フォーム、スコア表示、カード表現をダークテーマの制作アプリUIとして統一する。

## 非目標

- 既存API、永続化、LLM job、プロンプト編集、参照素材、結果レビューの機能仕様は変更しない。
- 画像生成サービスの自動操作や外部連携は追加しない。
- ユーザー可視UIに特定のMidjourneyバージョン番号を追加しない。
- 添付画像に存在しない新規機能や新しい情報設計は追加しない。

## 対象範囲

- `client/src/app/styles.css` を中心とした共通ビジュアルテーマ。
- 既存Reactコンポーネントのクラス構造に沿った、Composer / Free Editor / Matrix Lab / Reference Library / Result Review / Settings の表示調整。
- 必要最小限のコンポーネントclass追加または構造調整。
- README / docs の更新要否確認。

## マイルストーン

- [x] Task: 既存UI構造、CSS、主要画面コンポーネントを棚卸しする。
- [x] Task: スクリーンショット由来の共通デザイントークン、ダークテーマ、パネル、フォーム、ボタン、タブ、テーブル、カードを実装する。
- [x] Task: 主要画面ごとの密度、2-3カラム構成、Inspector / Sidebar / Statusbar 表現を添付画像に近づける。
- [x] Task: ローカル表示を起動してスクリーンショット確認し、崩れや読みにくさを修正する。
- [x] Task: lint / typecheck / test / build を実行し、機能非破壊を確認する。
- [x] Task: README、docs、gitignore、AGENTS更新要否を確認し、必要な場合のみ更新する。

## 受け入れ条件

- [x] 条件: アプリ全体が添付画像と同系統の深いネイビー系ダークUI、青紫アクセント、緑ステータス、黄警告、細い境界線、低彩度パネルで統一されている。
- [x] 条件: Composer / Free Editor / Reference Library / Result Review / Settings の既存操作導線が残っている。
- [x] 条件: 長文入力、テーブル、カード、スコア、サイドバー、右Inspectorで文字が重ならず、ボタン内テキストが収まる。
- [x] 条件: ユーザー可視UIに特定のMidjourneyバージョン番号を追加していない。
- [x] 条件: 既存テスト、型検査、ビルドが成功する。

## 検証コマンド

- `make lint`
- `make typecheck`
- `make test`
- `make build`

## 既知 blocker

- なし

## feature flag / rollback

- 見た目中心の変更として実装し、通常のgit revertで戻せる単位にまとめる。

## 検証記録

| 日時 | コマンド | 結果 | メモ |
|---|---|---|---|
| 2026-05-26 | `npm run typecheck` | Pass | Reactタブアイコン追加とCSS差し替え後の型検査。 |
| 2026-05-26 | ローカル表示確認 | Pass | Composer / Free Editor / Matrix Lab / Reference Library / Result Review / Settings を1680x945でスクリーンショット確認。 |
| 2026-05-26 | `make client-lint` | Pass | ESLint。 |
| 2026-05-26 | `make client-typecheck` | Pass | TypeScript型検査。 |
| 2026-05-26 | `make client-test` | Pass | Vitest 2 files / 3 tests。 |
| 2026-05-26 | `make client-build` | Pass | Vite production build。 |
| 2026-05-26 | `make lint` | Pass | Ruff。 |
| 2026-05-26 | `make typecheck` | Pass | mypy。 |
| 2026-05-26 | `make test` | Pass | pytest 28 passed。 |
| 2026-05-26 | `make build` | Pass | Python compileall。 |
| 2026-05-26 | `make e2e` | Pass | Playwright core local workflow parity。 |
| 2026-05-26 | `python3 scripts/verify_ui_text.py` | Fail | 通常Pythonでは`mj_prompt_studio`のimport pathが未設定。`.venv/bin/python`で再実行。 |
| 2026-05-26 | `.venv/bin/python scripts/verify_ui_text.py` | Pass | UI文言ポリシー確認。 |
| 2026-05-26 | `rg "V[0-9]\|v[0-9]\|Version [0-9]\|Midjourney V" client/src docs plans -n` | Pass | 該当なし。 |
| 2026-05-26 | ドキュメント更新要否確認 | Pass | README / gitignore / AGENTS は変更不要。UI仕様のみビジュアルデザイン方針を追記。 |
