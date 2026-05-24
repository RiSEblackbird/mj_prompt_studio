# 長大タスク実行手順

## 開始時

1. `AGENTS.md`、直近git履歴、作業ツリー状態を確認する。
2. `plans/TEMPLATE.md` をもとに `plans/<task-id>.md` を作成または更新する。
3. 目的、非目標、対象範囲、受け入れ条件、検証コマンド、blocker、rollback方針を明示する。
4. 既存の `Makefile`、`scripts/`、READMEから検証入口を確認する。

## 進行中

- 不明点は致命的でなければ仮定としてplanへ残し、実装を進める。
- Task内のマイルストーンごとに必要なlint、typecheck、test、buildを実行する。
- 失敗を認識したまま次へ進まず、修正またはBlockedとして整理する。
- UI、Application、Domain、Infra、LLMの責務を混在させない。

## 停止条件

- 外部依存、権限不足、環境障害、要件衝突、破壊的変更判断、秘密情報不足で実質的に進行不能な場合のみ停止する。
- 停止時はplanの項目をDone、Blocked、Cancelledへ整理し、再開条件と次の最短アクションを記録する。

## 完了時

1. 受け入れ条件をDoneまたは理由付きBlockedへ整理する。
2. 検証コマンドと結果をplanへ記録する。
3. READMEとdocsが実装に追従していることを確認する。
4. 不要ファイル、APIキー、DB、cache、log、画像アセットがgit追跡されていないことを確認する。
