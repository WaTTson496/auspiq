# 設定と保存物を扱う

このガイドは、設定ファイル、ログ、結果ファイル、ジョブ台帳を扱うためのものです。

## 設定を確認する

```bash
auspiq config show
auspiq config check
```

よく使う変更:

```bash
auspiq config set model gpt-4
auspiq config set threshold 85
auspiq config set generation-mode high_quality
```

補足:

- キー名はハイフンでもアンダースコアでも指定できます
- `practice` の既定閾値は固定 `80` で、`config.threshold` を自動では読みません
- `config show` は設定ファイルと環境変数の状況を見せますが、実行系コマンドがどちらを本当に使うかは別途理解しておく必要があります

## 設定ファイルの場所を把握する

- 既定: `~/.auspiq.json`
- 変更したいとき: グローバルオプション `--config-file`

## ログを確認する

- 既定のログ出力先: `logs/auspiq_YYYYMMDD_HHMMSS.log`
- ログレベルの指定:

```bash
auspiq --log-level DEBUG predict single "..."
```

環境変数:

- `CONSOLE_LOG_LEVEL`
- `FILE_LOG_LEVEL`

ログは、設定読込、API 呼び出し、保存先、失敗箇所の切り分けに使います。特に `predict batch` や生成の条件調整では、画面表示だけよりログの方が原因を追いやすいことがあります。

注意:

- `setup_logging()` 自体は上記環境変数を読めます
- ただし通常の `auspiq` 実行では、`cli.py` が設定ファイルまたは既定値を明示的に渡して初期化するため、これらの環境変数は通常経路では実質的に効きません

## 結果ファイルの場所を把握する

- `predict single`: `results/auspiq_single_YYYYMMDD_HHMMSS.json`
- `predict full`: `results/auspiq_full_YYYYMMDD_HHMMSS.json`
- `predict batch`: `results/auspiq_batch_YYYYMMDD_HHMMSS.json`
- `generate`: `--output` を付けたときだけ保存
- `practice --feedback-out`: 指定したパスへ保存

## ジョブ台帳を扱う

- Batch API と複数生成は `~/.auspiq-jobs.json` を使います
- 非同期処理の再取得では、この台帳と元入力ファイルの両方が必要です

予測 batch のジョブ記録に含まれる項目:

- `job_id`
- `input_file`
- `mode`
- `step`
- `min_length`
- `questions_count`
- `created_at`
- `job_type`
- `status`
- `completed_at`
- `output_file`
- `error_message`
- `metadata`

ジョブ台帳は実行履歴の完全な台帳ではなく、再取得や状態確認のためのローカル補助情報です。外部システムの authoritative source ではないので、ファイル移動や手動編集には注意してください。

## 関連

- 正確な設定キー一覧は [../reference/shared.md](../reference/shared.md)
- 失敗時の確認先は [troubleshooting.md](./troubleshooting.md)
