# ランタイム成果物

このページは、AuspiQ が実行時に生成・保存するファイル、job 台帳、SQLite schema、runtime object を定義するものです。

## ファイルシステム上の成果物

- `~/.auspiq.json`
  設定ファイルです。
- `~/.auspiq-jobs.json`
  `predict batch` と複数 `generate` の job 台帳です。
- `logs/auspiq_YYYYMMDD_HHMMSS.log`
  通常 CLI 実行のログファイルです。
- `results/auspiq_single_*.json`
- `results/auspiq_full_*.json`
- `results/auspiq_batch_*.json`
- `logs/raw_batch_results_<job_id>_<timestamp>.json`
- `results/generated_questions.sqlite3`

保存実態:

- `predict` は自動保存します。
- `generate` は `--output` があるときだけファイル保存します。
- SQLite store は実装されていますが、通常の `generate` CLI は store を pipeline に注入していないため、既定経路では `results/generated_questions.sqlite3` を更新しません。

## ジョブ台帳 `~/.auspiq-jobs.json`

トップレベルは `job_id -> job object` の object です。job object のキー:

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

`job_type` の値:

- `predict`
- `generate`

`metadata` の内容:

- `predict`
  実装上は追加 metadata を必須にしていません。
- `generate`
  `settings`、`output_format`、`output_level`、`output_path`、完了後の `summary` を持ちます。

## 生成実行時オブジェクト一覧

- `GenerationEvent`
- `GenerationResult`
- `GenerationFailure`
- `BatchProgress`
- `BatchGenerationResult`

実行経路との関係:

- `GenerationResult` は生成物本体、quality report、selection record、weight selection、metadata を束ねる中心 object です。
- `GenerationFailure` は batch 実行時の失敗 1 件を表します。
- `BatchGenerationResult` は `results`、`failures`、`progress` を束ねます。

## 生成メタデータ

生成 detail JSON や job metadata に現れる `metadata` object には次のキー群が入ります。

- `run_id`
- `created_at`
- `stage`
- `selection`
- `weight`
- `request`
- `timings`
- `prompt`

## SQLite スキーマ

table: `generated_questions`

columns:

- `record_id`: TEXT PRIMARY KEY
- `question`: TEXT NOT NULL
- `answer`: TEXT NOT NULL
- `question_type`: TEXT NOT NULL
- `facet_subject`: TEXT
- `facet_place`: TEXT
- `facet_time`: TEXT
- `facet_type`: TEXT
- `facet_codes`: TEXT NOT NULL
- `quality_report`: TEXT NOT NULL
- `metadata`: TEXT NOT NULL
- `created_at`: TEXT NOT NULL
- `score`: REAL NOT NULL
- `has_error`: INTEGER NOT NULL

indexes:

- `question_type`
- `created_at`
- `score`
- `has_error`
- `facet_subject`
- `facet_place`
- `facet_time`
- `facet_type`

## `GeneratedQuestionStore` API 一覧

- `save_record(record)`
- `save_records(records)`
- `get_record(record_id)`
- `list_records(limit=None)`
- `search_records(...)`

`search_records` の引数と意味:

- `text_query: str | None`
  `question LIKE %text_query% OR answer LIKE %text_query%` です。完全一致ではなく部分一致です。
- `question_type: str | None`
  `question_type = ?` の完全一致です。
- `facet_codes: Mapping[str, str] | None`
  対象は `subject`、`place`、`time`、`type` の 4 facet です。各 facet は対応カラムへの完全一致です。
- `min_score: float | None`
  `score >= min_score`
- `max_score: float | None`
  `score <= max_score`
- `has_error: bool | None`
  `has_error = 1/0`
- `created_from: str | None`
  `created_at >= created_from`
- `created_to: str | None`
  `created_at <= created_to`
- `limit: int | None`
  `ORDER BY created_at DESC LIMIT limit`

並び順:

- `list_records` も `search_records` も `created_at DESC` です。
