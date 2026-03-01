# 生成設定

このページは、`GenerationSettings`、`QualityCriteria`、`FacetWeightAdjuster`、built-in mode、`settings-file` の契約を定義するものです。

## `GenerationSettings`

フィールド:

- `stage`
  integer。既定値は `0` です。config 経由では `0` 以上でなければなりません。
- `question_type`
  `SC`、`OV`、`None` のいずれかです。`None` は問題タイプを固定しないことを意味します。
- `extra_instructions`
  `tuple[str, ...]` です。生成時に追加で埋め込む instruction です。
- `candidate_map`
  `Mapping[str, Sequence[str]] | None` です。facet 名ごとに選択候補コードを絞り込みます。内部では `str -> tuple[str, ...]` に正規化されます。
- `leaf_only`
  bool。`True` のときは leaf category のみを選択対象にします。
- `retry_count`
  integer。既定値は `2` です。`0` 以上でなければなりません。
- `retry_delay`
  float。既定値は `1.0` です。`0` 以上でなければなりません。
- `quality`
  `QualityCriteria` です。
- `prompt_template_path`
  `Path | None` です。指定時は `Path` に正規化されます。
- `weight_adjuster`
  `FacetWeightAdjuster | None` です。
- `parallelism`
  integer または `None` です。CLI/config 経由では `1..32` を要求します。

`GenerationSettings.__post_init__` が保証すること:

- `retry_count >= 0`
- `retry_delay >= 0`
- `quality.min_score` があるなら `0..100`
- `extra_instructions` は文字列タプル化
- `candidate_map` は文字列 key / 文字列タプル値へ正規化

## `QualityCriteria`

- `length_target`
  integer。既定値は `80` です。
- `length_tolerance`
  integer。既定値は `30` です。
- `min_score`
  float または `None`。`None` は品質足切りなしを意味します。指定時は `0..100` でなければなりません。

## `FacetWeightAdjuster`

- `facet_multipliers`
  `facet -> float` です。
- `code_multipliers`
  `facet -> code -> float` です。

解釈:

- 実効倍率は `facet_multipliers[facet] * code_multipliers[facet][code]` です。
- 片方が未指定なら `1.0` として扱います。
- 実効倍率が負値になると `GenerationSettingsError` です。
- CLI から与える倍率は `0` 以上でなければなりません。

## 内蔵モード

- `standard`
  `GenerationSettings()` をそのまま使います。
- `high_quality`
  `retry_count=4`、`quality.min_score=70.0`、追加 instruction 2 件を持ちます。

追加 instruction の実体:

- `情報の整合性と一意性が高まるように注意する`
- `問題文の特徴量を過不足なく盛り込む`

## 設定のマージ順序

1. built-in mode
2. config の `generation_*`
3. `--settings-file`
4. CLI overrides

各層で上書きされる内容:

- config は `generation_stage`、`generation_question_type`、`generation_retry_count`、`generation_retry_delay`、`generation_parallelism`、`generation_length_target`、`generation_length_tolerance`、`generation_min_score` を反映します。
- `--settings-file` はその JSON に含まれるキーだけを上書きします。
- CLI は `--question-type`、明示 `--stage`、`--length-target`、`--length-tolerance`、`--parallelism`、`--facet-weight`、`--code-weight` を上書きします。

`--mode` と `--quality` の解釈:

- `--quality high` は `mode=high_quality`
- `--quality standard` は `mode=standard`
- 両者が矛盾すると `click.ClickException`
- 両者が未指定のときだけ `config.generation_mode` を採用

## どの設定がどこに効くか

- selection
  `stage`、`candidate_map`、`leaf_only`、`weight_adjuster`
- prompt
  `question_type`、`extra_instructions`、`prompt_template_path`
- quality evaluation
  `quality.length_target`、`quality.length_tolerance`、`quality.min_score`
- retry
  `retry_count`、`retry_delay`
- batch execution
  `parallelism`

## `settings-file` の JSON 形式

```json
{
  "stage": 0,
  "question_type": "SC",
  "extra_instructions": ["..."],
  "candidate_map": {
    "subject": ["004"]
  },
  "leaf_only": true,
  "retry_count": 2,
  "retry_delay": 1.0,
  "parallelism": 4,
  "prompt_template_path": "path/to/template.md",
  "quality": {
    "length_target": 90,
    "length_tolerance": 20,
    "min_score": 70
  },
  "weight_adjuster": {
    "facet_multipliers": {
      "subject": 1.2
    },
    "code_multipliers": {
      "subject": {
        "004": 0.8
      }
    }
  }
}
```

解釈規則:

- JSON object 必須です。配列や文字列は不可です。
- `quality` は object 必須です。そうでなければエラーです。
- `weight_adjuster` は object 必須です。そうでなければエラーです。
- `facet_multipliers` と `code_multipliers` は object 必須です。
- `code_multipliers.<facet>` も object 必須です。
- 未知キーは無視されます。`settings-file` 側には `extra="forbid"` 相当の検証はありません。
