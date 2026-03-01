# 共通仕様リファレンス

このページは、グローバルオプション、設定ファイル、環境変数、保存物、`config` サブコマンドの仕様を定義するものです。

## グローバルオプション

- `--verbose`, `-v`
  コンソールログレベルを `DEBUG` に固定します。ファイルログレベルは変えません。
- `--config-file`, `-c <path>`
  既定の `~/.auspiq.json` の代わりに使う設定ファイルパスです。ルート CLI で指定した値は各サブコマンドに渡されます。`config` サブコマンド自身の `--config-file` を併用した場合は、サブコマンド側の値が優先されます。
- `--log-level`, `-l <level>`
  コンソールログレベルとファイルログレベルの両方を同じ値で上書きします。許可値は `DEBUG`、`INFO`、`WARNING`、`ERROR`、`CRITICAL` です。

## 設定ファイル

- 既定パス: `~/.auspiq.json`
- 形式: UTF-8 の JSON object
- ファイル未存在時: 内蔵既定値を in-memory で使います。ファイルは自動作成しません。
- 未知キー: 読み込み失敗になります。設定モデルは未知キーを許可しません。

設定キーと制約:

- `api_key`
  型は string または `null` です。`config set` では文字列として保存します。`config show/check` では環境変数より優先されます。
- `model`
  型は string です。既定値は `gpt-4` です。`config set` では値域検証を行いません。
- `threshold`
  型は integer、既定値は `80`、`config set` の許可範囲は `0..100` です。
- `max_tokens`
  型は integer、既定値は `2000`、`config set` では `1` 以上が必要です。
- `temperature`
  型は float、既定値は `0.1`、`config set` の許可範囲は `0.0..2.0` です。
- `console_log_level`
  型は string、既定値は `INFO`、許可値は `DEBUG|INFO|WARNING|ERROR|CRITICAL` です。
- `file_log_level`
  型は string、既定値は `DEBUG`、許可値は `DEBUG|INFO|WARNING|ERROR|CRITICAL` です。
- `generation_mode`
  型は string、既定値は `standard`、許可値は `standard|high_quality` です。
- `generation_question_type`
  型は string または `null`、既定値は `null`、許可値は `SC|OV` です。
- `generation_stage`
  型は integer、既定値は `0`、`0` 以上が必要です。
- `generation_length_target`
  型は integer、既定値は `80`、許可範囲は `1..300` です。
- `generation_length_tolerance`
  型は integer、既定値は `30`、許可範囲は `0..300` です。
- `generation_min_score`
  型は float または `null`、既定値は `null`、許可範囲は `0..100` です。
- `generation_retry_count`
  型は integer、既定値は `2`、`0` 以上が必要です。
- `generation_retry_delay`
  型は float、既定値は `1.0`、`0` 以上が必要です。
- `generation_parallelism`
  型は integer または `null`、既定値は `null`、許可範囲は `1..32` です。

## 設定の適用順序

共通設定の優先順序:

1. CLI オプション
2. 設定ファイル
3. 内蔵既定値

`generate` だけはさらに層が増えます。

1. built-in mode
2. 設定ファイルの `generation_*`
3. `--settings-file`
4. 明示 CLI オプション

`--mode` と `--quality` は同義です。両方を矛盾して指定するとエラーになります。両方とも明示していないときだけ `config.generation_mode` が使われます。

## 環境変数

- `OPENAI_API_KEY`
  `config show` と `config check` では fallback として参照されます。実行系コマンドの通常経路では `config.api_key` を使って `OpenAIClient` を初期化するため、環境変数だけでは `predict` / `generate` / `practice` 実行時の API キー源になりません。
- `CONSOLE_LOG_LEVEL`
- `FILE_LOG_LEVEL`

`CONSOLE_LOG_LEVEL` と `FILE_LOG_LEVEL` は logging の既定値として参照されますが、通常の CLI 実行では設定ファイルまたは `--log-level` の値が明示的に渡されるため、実行時に効くのはその明示値です。

## 保存物

- 設定ファイル: `~/.auspiq.json`
- ジョブ台帳: `~/.auspiq-jobs.json`
- ログファイル: `logs/auspiq_YYYYMMDD_HHMMSS.log`
- `predict single` の既定保存先: `results/auspiq_single_YYYYMMDD_HHMMSS.json`
- `predict full` の既定保存先: `results/auspiq_full_YYYYMMDD_HHMMSS.json`
- `predict batch` の既定保存先: `results/auspiq_batch_YYYYMMDD_HHMMSS.json`
- `predict batch --retrieve` の既定保存先: `results/auspiq_batch_<job_id先頭8文字>_<timestamp>.json`
- `predict batch --save-raw-results` の追加保存先: `logs/raw_batch_results_<job_id>_<timestamp>.json`
- `practice --feedback-out` の保存先: 指定したパス
- `generate --output` の保存先: 指定したパス

保存規則:

- `predict` は `--output` 未指定でも自動保存します。
- `generate` は `--output` を付けたときだけ保存します。自動保存はありません。
- `practice` は `--feedback-out` を付けたときだけフィードバック JSON を保存します。

## ジョブ台帳 `~/.auspiq-jobs.json`

トップレベルは `job_id -> job object` の JSON object です。各 job object は次のキーを持ちます。

- `job_id`: string
- `input_file`: string。`predict batch --submit` では絶対パスが保存されます。
- `mode`: string。`predict` では `single|full`、`generate` では生成 mode 名です。
- `step`: integer
- `min_length`: integer
- `questions_count`: integer
- `created_at`: ISO 8601 string
- `job_type`: string。`predict` または `generate`
- `status`: string
- `completed_at`: ISO 8601 string または `null`
- `output_file`: string または `null`
- `error_message`: string または `null`
- `metadata`: object

`predict batch --status` と `predict batch --retrieve` は、このローカル記録に対象 job があることを前提に動きます。任意の OpenAI job id を直接指定して使うことはできません。

## `config` サブコマンド

- `config show`
  現在値を表示します。`--show-sensitive` を付けると API キーを伏せずに表示します。設定ファイルに API キーがなく環境変数がある場合は、環境変数由来であることが表示されます。
- `config set <key> <value>`
  指定キーを更新します。`key` 内の `-` は `_` に正規化されます。受理キーは `api_key`、`model`、`threshold`、`max_tokens`、`temperature`、`console_log_level`、`file_log_level`、`generation_mode`、`generation_question_type`、`generation_stage`、`generation_length_target`、`generation_length_tolerance`、`generation_min_score`、`generation_retry_count`、`generation_retry_delay`、`generation_parallelism` です。
- `config reset`
  確認プロンプトの後、既定値一式をファイルへ書き戻します。
- `config delete`
  確認プロンプトの後、設定ファイル自体を削除します。
- `config check`
  設定の妥当性を確認します。

`config check` が検証する項目:

- API キーの存在
- API キーが `sk-` で始まるか
- API キーがあれば OpenAI API で `model` を検証
- `threshold`
- `console_log_level`
- `file_log_level`
- `generation_mode`
- `generation_question_type`
- `generation_stage`
- `generation_length_target`
- `generation_length_tolerance`
- `generation_min_score`
- `generation_retry_count`
- `generation_retry_delay`
- `generation_parallelism`

`config check` が検証しない項目:

- `max_tokens` の正値制約
- `temperature` の `0.0..2.0` 制約
- 実行系コマンドが環境変数 API キーだけで動くかどうか

## 実装差異として把握しておくべき点

- `config.threshold` は設定に存在しますが、`practice` の既定値には使われません。`practice` の既定閾値は常に `80` です。
- `practice` は設定ファイルを読み込みますが、現状その値を練習動作に反映していません。
- `predict single` の保存は常に JSON です。`--format` は画面表示だけを切り替えます。
- `predict full` と `predict batch` は保存先拡張子で形式が変わります。`.json` は完全 JSON、`.txt` / `.text` は統計テキスト、それ以外や拡張子なしは実ファイル名が `.json` に変わります。
