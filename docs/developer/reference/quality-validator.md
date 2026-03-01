# 品質バリデータ

このページは、`quality_validator.py` が出す issue と score の計算規則を定義するものです。

## 問題一覧

- `question.empty`
- `answer.empty`
- `question.language`
- `question.length`
- `question.type_mismatch`
- `question.type_unknown`
- `question.ending`
- `answer.leak`
- `answer.multiple`
- `answer.non_noun`
- `facet.missing`
- `facet.unknown`

## 重大度

- `error`
- `warning`
- `info`

## 問題タイプ検出

正規表現:

- `SC`
  `(何|誰)(でしょう|ですか)\s*[?？]?$`
- `OV`
  `(何と|なんと).*(いう|呼ぶ|称する)(でしょう|ですか)\s*[?？]?$`

解釈:

- 指定 `question_type` が `SC|OV` 以外なら `QualityValidationError`
- 指定型があり、検出型があり、両者が異なれば `question.type_mismatch`
- 指定型があり、検出型が取れなければ `question.type_unknown`

## 各検査条件

- `question.empty`
  `question.strip()` が空
- `answer.empty`
  `answer.strip()` が空
- `question.language`
  問題文に日本語文字が含まれない
- `question.length`
  長さが `length_target ± length_tolerance` から外れる
- `question.ending`
  `?`、`？`、`でしょう`、`ですか` のいずれでも終わらない
- `answer.leak`
  正規化した解答文字列が問題文内に含まれる
- `answer.multiple`
  `/`、`／`、`、`、`・`、`または`、`もしくは`、`又は` のいずれかを含む
- `answer.non_noun`
  `する`、`した`、`している`、`なる`、`なった`、`です` のいずれかで終わる
- `facet.missing`
  `subject`、`place`、`time`、`type` のうち不足がある
- `facet.unknown`
  `facet_manager.get_category(facet, code)` が取れない

## スコア計算

component:

- `length`
- `structure`
- `answer`

計算手順:

1. `length_score` を計算
2. `structure_score` を計算
3. `answer_score` を計算
4. 3 成分の平均を base にする
5. issue ごとの penalty を引く
6. `0.0` 未満にならないよう丸める
7. 小数 1 桁で丸める

component の式:

- `length_score`
  - 長さ `<= 0` なら `0.0`
  - 目標範囲内なら `100.0`
  - 範囲外なら `max(0.0, 100.0 - abs(length - target) * 1.5)`
- `structure_score`
  - 検出型なしなら `50.0`
  - 指定型なしなら `80.0`
  - 検出型と指定型一致なら `100.0`
  - 不一致なら `70.0`
- `answer_score`
  - `answer.leak` があれば `0.0`
  - それ以外で `answer.multiple` があれば `70.0`
  - それ以外は `100.0`

penalty:

- `error`: `25.0`
- `warning`: `10.0`
- `info`: `2.0`

## 出力構造

`QuestionQualityReport.as_dict()` の shape:

- `question`: string
- `answer`: string
- `question_type`: `SC|OV|null`
- `detected_type`: `SC|OV|null`
- `length`: integer
- `facet_codes`: object または `null`
- `issues`: array
- `score`: object

`issues[]` の shape:

- `code`: string
- `message`: string
- `severity`: string
- `field`: string または省略

`score` の shape:

- `total`: float
- `components.length`: float
- `components.structure`: float
- `components.answer`: float

## 制限

- semantic consistency は検査しません。
- facet code の存在確認まではしますが、題材がその交点に本当に属するかは判定しません。
