# Security and Privacy

## APIキー

- `OPENAI_API_KEY` は端末の環境変数またはOS資格情報ストアから読む。
- 互換用に `OPENAI_KEY` と `MJPS_OPENAI_API_KEY` も環境変数として読み取れる。
- 平文設定ファイルへの保存は既定にしない。
- Job、ログ、エクスポート、スクリーンショットにAPIキーを出さない。

## ローカル資産

- 参照画像と生成結果画像はユーザーが手動で取り込む。
- asset storeはローカルアプリデータ領域に作成する。
- 画像そのもの、DB、cache、log、export、API response dumpはgit追跡対象外。

## 外部送信

- 画像解析や結果レビューを実行した場合のみ、必要な画像と最小限のメタデータをLLMへ渡す。
- Privacy modeではResponses APIの保存を無効化し、会話ID継続を使わない。

## 生成サービス境界

禁止:

- Web/Discord/Botの自動操作。
- ログイン自動化。
- Cookie、Token、Session取得。
- 非公式API、自動投稿、ブラウザ自動クリック。

許可:

- ユーザーによる手動コピー、手動貼り付け、手動アップロード。
- ユーザーがローカルへ保存した画像の手動取り込み。
