# 練習リファレンス

このページは、`practice` コマンドの入力、オプション、操作、フィードバック JSON を定義するものです。

## コマンド構文

```bash
auspiq practice --file PATH [--threshold N] [--speed SEC] [--start-from N] [--limit N] [--feedback-out PATH]
```

## オプション一覧

- `--file`, `-f`
  必須です。存在する JSON ファイルでなければなりません。
- `--threshold`, `-t`
  自動一時停止の閾値です。既定値は `80` です。help には `0-100` と書かれていますが、CLI では範囲検証をしていません。内部では `analysis_point.total_probability >= threshold` の整数比較として使います。
- `--speed`, `-s`
  文字表示速度です。既定値は `0.1` 秒/文字です。範囲検証はありませんが、内部では `max(0.01, speed)` に丸めるため、`0.01` 未満や負値でも最終的に `0.01` 秒/文字になります。
- `--start-from`, `-n`
  開始インデックスです。既定値は `0` です。範囲検証はありません。全問題構築後の Python slice にそのまま渡されるため、負値は負 index として解釈されます。
- `--limit`, `-l`
  最大問題数です。未指定時は末尾まで使います。範囲検証はありません。`start_from + limit` が slice の終了位置になります。
- `--feedback-out`
  練習結果を JSON 保存するパスです。

## 入力形式

`practice` が受け付けるのは JSON のみです。CSV は受け付けません。

受理する JSON:

- `predict full` / `predict batch` の解析結果
  トップレベルが `{"questions":[...]}` の形式です。
- `generate` 単発 JSON
  トップレベルに `question` と `answer` を持つ形式です。
- `generate` 複数生成 JSON
  トップレベルに `results` を持つ形式です。

受理しない JSON:

- `predict single` の保存 JSON
- 単純な JSON 配列
- 独自の任意 object

## 入力形式ごとの変換

解析結果 JSON の場合:

- 各 `questions[]` が `PracticeQuestion` に変換されます。
- `question.original_text` が問題文になります。
- `question.correct_answer` が解答になります。
- `analysis_points` がそのまま使われます。
- 解答が空だとエラーです。
- `metadata.source_format` には `analysis_results` が入ります。

生成単発 JSON の場合:

- 問題文は `question`、解答は `answer` です。
- `analysis_points` は空配列になります。
- `metadata.source_format` は `generation_single` です。
- `metadata.question_type`、`metadata.facet_codes`、`metadata.generation_metadata`、`metadata.quality_report`、`metadata.facet_labels` が引き継がれます。

生成複数 JSON の場合:

- `results[]` の各要素が練習問題になります。
- `analysis_points` は空配列になります。
- `metadata.source_format` は `generation_batch` です。
- 各結果の `question_type`、`facet_codes`、`metadata`、`quality_report`、`facet_labels` が引き継がれます。

重要な差異:

- 解析結果入力では `analysis_points` があるので閾値ベースの自動停止が動きます。
- 生成結果入力では `analysis_points=[]` なので `--threshold` は実質無効です。

## 練習中の操作

練習開始前:

- `[Enter]`
  現在の問題を開始します。
- `q` または `quit`
  練習全体を終了し、結果表示へ進みます。

問題文表示中:

- `[Enter]`
  一時停止し、プレイヤーが解答権を獲得します。
- `a`
  解答表示に進みます。
- `n`
  その問題を `skip` として記録し、次の問題へ進みます。
- `q`
  練習全体を終了します。

解答権獲得後:

- `[Enter]`
  解答入力に進みます。
- `c`
  解答権を破棄して問題文表示を再開します。

自動停止後:

- システムが解答権を獲得します。
- `[Enter]` でシステム判定に進みます。
- `c` で問題文表示を継続します。

解答入力時:

- `c` または `correct`
  正解として記録します。
- `i` または `incorrect`
  不正解として記録します。
- `s` または `skip`
  スキップとして記録します。

システム解答権時の判定入力:

- `[Enter]`
  自動判定です。現在位置の `total_probability` を確率として正誤を決めます。該当蓋然性がない場合は 50% ランダムです。
- `c`
  システム正解として記録します。
- `i`
  システム不正解として記録します。

## 自動停止

発火条件:

- 現在表示位置と完全一致する `analysis_point.position` がある
- その `analysis_point.total_probability >= threshold`
- その問題ですでに自動停止が起きていない

発火後の挙動:

- 問題表示を停止します。
- システムが解答権を獲得します。
- その問題では以後の自動停止を無効化します。

## フィードバック JSON

`--feedback-out` を指定したときの保存形式:

```json
{
  "created_at": "2026-02-28T12:34:56.789012",
  "source_file": "results/input.json",
  "source_format": "analysis_results",
  "summary": {
    "total_questions": 3,
    "correct_answers": 2,
    "incorrect_answers": 1,
    "skipped_questions": 0,
    "average_push_position": 24.0,
    "total_time": 31.4,
    "accuracy_rate": 66.7
  },
  "entries": [
    {
      "question": "問題文",
      "correct_answer": "解答",
      "result": "correct",
      "push_position": 20,
      "time_taken": 8.2,
      "question_type": "SC",
      "facet_codes": {
        "subject": "004"
      },
      "source_metadata": {
        "source_format": "generation_single"
      }
    }
  ]
}
```

各フィールド:

- `created_at`
  ISO 8601 string です。
- `source_file`
  入力ファイルパスです。
- `source_format`
  セッション内で最初に見つかった入力種別です。`analysis_results`、`generation_single`、`generation_batch` のいずれかです。
- `summary.total_questions`
  記録された解答数です。
- `summary.correct_answers`
- `summary.incorrect_answers`
- `summary.skipped_questions`
- `summary.average_push_position`
- `summary.total_time`
- `summary.accuracy_rate`
- `entries`
  問題ごとの結果配列です。
- `entries[].question`
- `entries[].correct_answer`
- `entries[].result`
  `correct`、`incorrect`、`skip` のいずれかです。
- `entries[].push_position`
  integer、`0` 以上です。
- `entries[].time_taken`
  float、`0` 以上です。
- `entries[].question_type`
  生成由来なら入ることがあります。解析結果由来では通常 `null` です。
- `entries[].facet_codes`
  生成由来なら入ることがあります。
- `entries[].source_metadata`
  練習問題に載っていた metadata をそのまま持ち越した object です。

## 実装差異として把握しておくべき点

- `practice` は設定ファイルを読みますが、その値を練習挙動へ使っていません。
- `config.threshold` は `practice` 既定値に反映されません。
