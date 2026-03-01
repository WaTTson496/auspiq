# 生成リファレンス

このページは、`generate` コマンドの入力、設定解決、出力、保存、ジョブ記録を定義するものです。

## コマンド構文

```bash
auspiq generate [options]
```

## オプション一覧

- `--mode <standard|high_quality>`
  生成モードです。既定値は `standard` です。
- `--quality <standard|high>`
  `mode` の別名です。`high` は `high_quality`、`standard` は `standard` に対応します。`--mode` と矛盾して指定するとエラーです。
- `--question-type <SC|OV>`
  出力したい問題構文です。
- `--count`, `-n <1..1000>`
  生成数です。既定値は `1` です。
- `--batch-size <1..500>`
  複数生成時の chunk サイズです。`count < 2` で指定するとエラーです。
- `--parallelism <1..32>`
  複数生成時の並列数です。未指定時は `config.generation_parallelism`、それも未設定なら `min(4, count)` が使われます。
- `--stage <integer>`
  重みステージです。CLI 明示時は `0` 以上でなければなりません。既定値は `0` です。
- `--length-target <1..300>`
  品質評価で使う目標文字数です。
- `--length-tolerance <0..300>`
  品質評価で使う許容誤差です。
- `--settings-file <path>`
  生成設定 JSON です。存在するファイルでなければなりません。
- `--facet-weight facet=multiplier`
  ファセット単位の重み補正です。複数回指定できます。
- `--code-weight facet:code=multiplier`
  コード単位の重み補正です。`facet.code=multiplier` 形式も受け付けます。複数回指定できます。
- `--format <rich|text|json>`
  画面表示形式です。既定値は `rich` です。
- `--output`, `-o <path>`
  保存先です。未指定時はファイル保存しません。
- `--output-level <detail|brief>`
  出力に含める情報量です。既定値は `detail` です。
- `--log-level <DEBUG|INFO|WARNING|ERROR|CRITICAL>`
  このコマンドのコンソールログとファイルログを同時に上書きします。
- `--no-log-file`
  ログファイル出力を無効化します。

## モードと優先順位

built-in mode:

- `standard`
  `GenerationSettings()` の既定値です。
- `high_quality`
  `retry_count=4`、`quality.min_score=70.0`、追加 instruction 2 件を持つ mode です。

設定の解決順:

1. built-in mode
2. 設定ファイルの `generation_*`
3. `--settings-file`
4. 明示 CLI オプション

追加ルール:

- `--mode` と `--quality` が両方とも明示されていなければ、`config.generation_mode` が使われます。
- `high_quality` の値も、その後に来る設定ファイルや `--settings-file`、CLI オプションで上書きされます。

## `--settings-file`

形式:

- UTF-8 の JSON object 必須です。
- object 以外はエラーです。

受理キー:

- `stage`
- `question_type`
- `extra_instructions`
- `candidate_map`
- `leaf_only`
- `retry_count`
- `retry_delay`
- `parallelism`
- `prompt_template_path`
- `quality`
- `weight_adjuster`

`quality` の受理キー:

- `length_target`
- `length_tolerance`
- `min_score`

`weight_adjuster` の受理形:

```json
{
  "facet_multipliers": {
    "subject": 1.2
  },
  "code_multipliers": {
    "subject": {
      "004": 0.8
    }
  }
}
```

正規化と制約:

- `question_type` は string として読み、最終的に `SC` または `OV` で使います。
- `extra_instructions` は文字列タプルへ正規化されます。
- `candidate_map` は `facet -> string sequence` へ正規化されます。
- `retry_count` は `0` 以上でなければなりません。
- `retry_delay` は `0` 以上でなければなりません。
- `quality.min_score` は `0..100` でなければなりません。
- `parallelism` は最終的に `1..32` である必要があります。
- `facet-weight` と `code-weight` は `settings-file.weight_adjuster` があればその上にマージされ、同じ facet/code を後から指定した値で上書きします。
- `facet` 名や `code` 名そのものの妥当性は CLI では検証しません。

## API 呼び出しに影響する設定

- 通常モデルでは `max_tokens` と `temperature` を送ります。
- `o1*` / `gpt-5*` 系では `max_completion_tokens=max(max_tokens, 3000)` に切り替わります。
- `o1*` と `gpt-5*` では `temperature` を送りません。

## 単発出力

`count=1` のときの JSON 出力は `GeneratedQuestionItem` です。

`brief` の完全形:

```json
{
  "question": "問題文",
  "answer": "解答",
  "question_type": "SC",
  "facet_codes": {
    "subject": "004"
  }
}
```

`detail` で追加されるフィールド:

- `facet_labels`
- `quality_report`
- `selection`
- `weight_selection`
- `metadata`

`detail` JSON の各フィールド:

- `question`
  string。
- `answer`
  string。
- `question_type`
  string。`SC` または `OV`。
- `facet_codes`
  object。`facet -> classification_code` です。
- `facet_labels`
  object。`facet -> label or null` です。
- `quality_report`
  object。詳細はこのページ下部の品質レポートを参照してください。
- `selection.combination_key`
  string。
- `selection.final_weight`
  float。
- `selection.steps`
  配列です。各要素は次のキーを持ちます。
  - `facet`
  - `classification_code`
  - `weight`
  - `probability`
  - `candidate_count`
- `weight_selection.weight`
  float。
- `weight_selection.weight_type`
  string。`single`、`double`、`triple`、または base fallback です。
- `weight_selection.base_weight`
  float。
- `weight_selection.stage`
  integer。
- `weight_selection.matched_entry`
  object または省略。対応する weight entry があるときだけ入ります。
- `metadata`
  object。トップレベルキーは `run_id`、`created_at`、`stage`、`selection`、`weight`、`request`、`timings`、`prompt` です。

## 複数生成出力

`count>1` の JSON 出力は次の shape です。

```json
{
  "summary": {
    "total": 10,
    "succeeded": 8,
    "failed": 2,
    "average_score": 73.4,
    "min_score": 55.0,
    "max_score": 91.0,
    "error_count": 1,
    "warning_count": 7
  },
  "results": [],
  "failures": [
    {
      "phase": "api_call",
      "message": "error text",
      "exception_type": "QuestionGenerationAPIError",
      "facet_codes": {
        "subject": "004"
      }
    }
  ]
}
```

各フィールド:

- `summary.total`
  要求生成数です。
- `summary.succeeded`
  成功件数です。
- `summary.failed`
  失敗件数です。
- `summary.average_score`
  成功結果の平均品質スコアです。成功 0 件なら `0.0` です。
- `summary.min_score`
  成功結果の最小品質スコアです。
- `summary.max_score`
  成功結果の最大品質スコアです。
- `summary.error_count`
  成功結果に含まれる `error` issue の総数です。
- `summary.warning_count`
  成功結果に含まれる `warning` issue の総数です。
- `results`
  単発出力の配列版です。`output-level=brief` なら brief shape、`detail` なら detail shape です。
- `failures[].phase`
  失敗フェーズです。
- `failures[].message`
  例外メッセージです。
- `failures[].exception_type`
  例外クラス名です。
- `failures[].facet_codes`
  失敗時点で確定していたファセットコードです。なければ `null` です。

## 品質レポート

`quality_report` は次の shape です。

```json
{
  "question": "問題文",
  "answer": "解答",
  "question_type": "SC",
  "detected_type": "SC",
  "length": 82,
  "facet_codes": {
    "subject": "004"
  },
  "issues": [
    {
      "code": "question.length",
      "message": "問題文の長さが目安を外れています。",
      "severity": "warning",
      "field": "question"
    }
  ],
  "score": {
    "total": 90.0,
    "components": {
      "length": 100.0,
      "structure": 100.0,
      "answer": 100.0
    }
  }
}
```

各フィールド:

- `question`
- `answer`
- `question_type`
- `detected_type`
- `length`
- `facet_codes`
- `issues`
- `score`

`issues[]` の各フィールド:

- `code`
  string。
- `message`
  string。
- `severity`
  `error`、`warning`、`info` のいずれかです。
- `field`
  string または省略です。

## 保存仕様

- 画面表示形式は `--format` で決まります。
- 保存は `--output` 指定時だけ行います。
- 親ディレクトリは自動作成されます。
- `--format rich` で保存する場合、保存内容は rich ではなく plain text です。
- `--format text` は plain text を保存します。
- `--format json` は JSON を保存します。
- `predict` と違って拡張子自動補正はありません。指定したパスへそのまま書きます。

## ジョブ記録

`count>1` のときは `~/.auspiq-jobs.json` に `job_type="generate"` の job を追加します。

`metadata` に保存される内容:

- `settings`
  その job に適用された生成設定です。
- `output_format`
- `output_level`
- `output_path`
- `summary`
  完了後に追加される生成サマリーです。

## 実装差異として把握しておくべき点

- CLI は SQLite store を通常経路で使いません。`results/generated_questions.sqlite3` は CLI 実行では更新されません。
- 自動保存はないため、生成結果を後で再利用するなら `--output` を自分で指定する必要があります。
