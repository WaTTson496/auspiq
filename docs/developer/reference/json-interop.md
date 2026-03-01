# JSON 相互運用

このページは、CLI 間で受け渡される JSON 契約を定義するものです。

## `predict single` 出力

型は `PredictionResponse` です。

トップレベルキー:

- `candidates`: array
- `total_probability`: integer `0..100`
- `text_so_far`: string

`candidates[]` のキー:

- `full_text`: string
- `answer`: string
- `probability`: integer `0..100`

`practice` はこの形式を受け付けません。

## `predict full` / `predict batch` 出力

トップレベルは次の shape です。

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

各キー:

- `questions`: array 必須
- `questions[].question`: object 必須
- `questions[].question.original_text`: string 必須
- `questions[].question.correct_answer`: string または `null`
- `questions[].analysis_points`: array 必須
- `questions[].analysis_points[].position`: integer `>= 0`
- `questions[].analysis_points[].text_so_far`: string 必須
- `questions[].analysis_points[].candidates`: array 必須
- `questions[].analysis_points[].candidates[]`: `PredictionCandidate`
- `questions[].analysis_points[].total_probability`: integer `0..100`

`practice` が解析結果として受理する判別条件は「トップレベルが object で `questions` キーを持つこと」です。さらに各問題に解答が必要です。

## `generate` 単発出力

型は `GeneratedQuestionItem` です。

`brief` で必須のキー:

- `question`: string
- `answer`: string
- `question_type`: string
- `facet_codes`: object

`detail` で追加されるキー:

- `facet_labels`: object または `null`
- `quality_report`: object または `null`
- `selection`: object または `null`
- `weight_selection`: object または `null`
- `metadata`: object または `null`

`practice` が生成単発として受理する判別条件は「トップレベルが object で `question` と `answer` を持つこと」です。`selection` や `quality_report` はなくても受理できます。

## `generate` 複数出力

トップレベル shape:

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

各キー:

- `summary`: object 必須
- `summary.total`: integer `>= 0`
- `summary.succeeded`: integer `>= 0`
- `summary.failed`: integer `>= 0`
- `summary.average_score`: float `>= 0`
- `summary.min_score`: float または `null`
- `summary.max_score`: float または `null`
- `summary.error_count`: integer `>= 0`
- `summary.warning_count`: integer `>= 0`
- `results`: array 必須。各要素は `GeneratedQuestionItem`
- `failures`: array 必須。各要素は object
- `failures[].phase`: string 必須
- `failures[].message`: string 必須
- `failures[].exception_type`: string 必須
- `failures[].facet_codes`: object または `null`

`practice` が生成 batch として受理する判別条件は「トップレベルが object で `results` キーを持つこと」です。

## `practice` 入力受理条件

`practice` が受け付けるのは次の 3 系統だけです。

- 解析結果: object かつ `questions` を持つ
- 生成単発: object かつ `question` と `answer` を持つ
- 生成複数: object かつ `results` を持つ

受け付けないもの:

- `predict single` JSON
- JSON array
- CSV
- 独自 object

## `practice` フィードバック出力

型は `PracticeFeedbackReport` です。

トップレベルキー:

- `created_at`: string 必須
- `source_file`: string または `null`
- `source_format`: string または `null`
- `summary`: object 必須
- `entries`: array 必須

`summary` のキー:

- `total_questions`: integer `>= 0`
- `correct_answers`: integer `>= 0`
- `incorrect_answers`: integer `>= 0`
- `skipped_questions`: integer `>= 0`
- `average_push_position`: float `>= 0`
- `total_time`: float `>= 0`
- `accuracy_rate`: float `0..100`

`entries[]` のキー:

- `question`: string 必須
- `correct_answer`: string または `null`
- `result`: string 必須
- `push_position`: integer `>= 0`
- `time_taken`: float `>= 0`
- `question_type`: string または `null`
- `facet_codes`: object または `null`
- `source_metadata`: object 必須

## 相互運用上の注意

- 解析結果を `practice` に渡すときは `question.correct_answer` が必要です。欠落していると失敗します。
- `generate` の detail JSON は end-user 向け出力であると同時に、developer が selection / weight / quality を観測するための JSON 契約でもあります。
