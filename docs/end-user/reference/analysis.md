# 解析リファレンス

このページは、`predict single`、`predict full`、`predict batch` の入力、出力、保存、制約を定義するものです。

## `predict single`

構文:

```bash
auspiq predict single TEXT [--max-candidates N] [--format table|json] [--output PATH]
```

引数とオプション:

- `TEXT`
  必須の位置引数です。空文字は受け付けません。
- `--max-candidates`, `-m`
  `1..10` の整数です。既定値は `5` です。
- `--format`
  `table` または `json` です。既定値は `table` です。画面表示だけを切り替えます。
- `--output`, `-o`
  保存先パスです。未指定時は `results/auspiq_single_YYYYMMDD_HHMMSS.json` です。

保存形式:

- 保存ファイルは常に JSON です。
- `--format table` を指定しても保存形式は変わりません。
- 指定パスの拡張子は解釈されません。指定したパスへそのまま JSON を書きます。

保存 JSON の完全形:

```json
{
  "candidates": [
    {
      "full_text": "完全な問題文",
      "answer": "解答",
      "probability": 42
    }
  ],
  "total_probability": 85,
  "text_so_far": "入力途中文/"
}
```

各フィールド:

- `candidates`
  配列です。各要素は推測候補です。
- `candidates[].full_text`
  string。候補となる完全問題文です。
- `candidates[].answer`
  string。候補問題文に対する解答です。
- `candidates[].probability`
  integer、`0..100`。候補ごとの蓋然性です。
- `total_probability`
  integer、`0..100`。候補全体の合計蓋然性です。
- `text_so_far`
  string。API に渡した途中文です。

## `predict full`

構文:

```bash
auspiq predict full TEXT [ANSWER] [--step N] [--min-length N] [--format table|json] [--output PATH]
```

引数とオプション:

- `TEXT`
  必須の位置引数です。完全な問題文を渡します。
- `ANSWER`
  任意の位置引数です。指定すると保存結果の `question.correct_answer` に入ります。未指定時は空文字列です。
- `--step`, `-s`
  `1..20` の整数です。既定値は `1` です。
- `--min-length`
  `1..50` の整数です。既定値は `1` です。
- `--format`
  `table` または `json` です。既定値は `table` です。画面表示だけを切り替えます。
- `--output`, `-o`
  保存先パスです。未指定時は `results/auspiq_full_YYYYMMDD_HHMMSS.json` です。

解析位置の作り方:

- 解析位置は `range(min_length, len(TEXT) - 5, step)` で計算されます。
- 問題文末尾 5 文字分は解析対象に含まれません。
- 問題文長が短い場合は解析位置が 0 件になることがあります。
- 各位置で API へ送る `max_candidates` は固定で `5` です。CLI から変更できません。

保存形式:

- `.json` 拡張子: 完全 JSON を保存します。
- `.txt` または `.text`: 統計テキストを保存します。
- それ以外の拡張子または拡張子なし: 実際に作られるのは `<指定パス>.json` です。

JSON 保存時の完全形:

```json
{
  "questions": [
    {
      "question": {
        "original_text": "問題文",
        "correct_answer": "解答"
      },
      "analysis_points": [
        {
          "position": 12,
          "text_so_far": "途中文/",
          "candidates": [
            {
              "full_text": "完全な問題文",
              "answer": "解答",
              "probability": 42
            }
          ],
          "total_probability": 85
        }
      ]
    }
  ]
}
```

各フィールド:

- `questions`
  配列です。`predict full` 単体でもこの配列形式で保存されます。
- `questions[].question.original_text`
  string。元の完全問題文です。
- `questions[].question.correct_answer`
  string または `null`。CLI では `ANSWER` を渡さないと空文字列で保存されます。
- `questions[].analysis_points`
  配列です。各解析位置の結果を持ちます。
- `questions[].analysis_points[].position`
  integer、`0` 以上。文字位置です。
- `questions[].analysis_points[].text_so_far`
  string。その位置までの入力文字列です。実装では末尾に `/` を付けて保存します。
- `questions[].analysis_points[].candidates`
  `predict single` の `candidates` と同じ shape です。
- `questions[].analysis_points[].total_probability`
  integer、`0..100`。

注意:

- `practice` に渡す解析結果では `question.correct_answer` が必要です。
- `.txt` 出力は `practice` 入力に使えません。

## `predict batch`

構文:

```bash
auspiq predict batch [--input PATH | --status JOB_ID | --retrieve JOB_ID | --list-jobs] [options]
```

アクション制約:

- `--input`
- `--status JOB_ID`
- `--retrieve JOB_ID`
- `--list-jobs`

この 4 つのうち、1 回の呼び出しで選べるのは厳密に 1 つだけです。0 個でも複数でもエラーです。

共通オプション:

- `--output`, `-o`
  保存先です。新規リアルタイム処理では未指定時に `results/auspiq_batch_YYYYMMDD_HHMMSS.json`、`--retrieve` では未指定時に `results/auspiq_batch_<job_id先頭8文字>_<timestamp>.json` が使われます。
- `--mode`
  `single` または `full` です。既定値は `single` です。
- `--step`, `-s`
  `full` 解析または `single` 中間位置計算に使います。`1..20`、既定値は `1` です。
- `--min-length`
  `1..50`、既定値は `1` です。
- `--use-batch-api`
  OpenAI Batch API を使う指定です。新規投入時にだけ意味があります。
- `--completion-window`
  現在は `24h` だけを受け付けます。
- `--submit`
  `--use-batch-api` と組み合わせて新規 batch job を投入します。
- `--save-raw-results`
  `--retrieve` 時だけ意味があります。raw 結果を追加保存します。

### `--input` で新規処理する場合

受理入力:

- JSON
- CSV

受理条件:

- 全問題に解答が必要です。解答欠落はエラーです。
- JSON は次の 3 形式だけを受け付けます。

```json
[
  { "question": "問題文", "answer": "解答" }
]
```

```json
{
  "results": [
    { "question": "問題文", "answer": "解答" }
  ]
}
```

```json
{
  "question": "問題文",
  "answer": "解答"
}
```

- `{"questions":[...]}` 形式の解析結果 JSON は batch 入力としては受け付けません。
- CSV は `question` 列必須、`answer` 列必須です。

`--mode single` の動作:

- 各問題の解析位置は `max(min_length, len(question) // 2)` です。
- 各問題で 1 回だけ推測します。
- 結果は `AnalysisResult` 形式へ変換されて保存されます。
- 候補数は固定で `5` です。

`--mode full` の動作:

- 各問題で `predict full` と同じ `range(min_length, len(text) - 5, step)` を走査します。
- 候補数は固定で `5` です。

Batch API 指定時の制約:

- `--use-batch-api` を付けたら `--submit` も必須です。
- `--submit` なしの `--use-batch-api` はエラーです。
- 提出時には `~/.auspiq-jobs.json` に job 記録を作ります。

### `--status JOB_ID`

- ローカル job 台帳に `JOB_ID` が存在することが前提です。
- OpenAI に直接問い合わせる前に、ローカル job 情報を参照します。
- 任意の OpenAI job id を単独で指定しても、ローカル記録がなければ使えません。

### `--retrieve JOB_ID`

- ローカル job 台帳に `JOB_ID` が存在することが前提です。
- 台帳に保存された `input_file` から元問題を再読込します。
- 元入力ファイルが失われていると取得に失敗します。
- `--save-raw-results` を付けた場合だけ `logs/raw_batch_results_<job_id>_<timestamp>.json` を追加保存します。

### `--list-jobs`

- `~/.auspiq-jobs.json` の直近 job 一覧を表示します。

保存 JSON の shape:

- 新規リアルタイム処理と `--retrieve` の保存結果は、どちらも `predict full` と同じ `{"questions":[...]}` 形式です。
