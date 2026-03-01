# ファセットデータと重みデータ

このページは、facet YAML と weight JSON の入力契約、検証条件、実行時解決順を定義するものです。

## ファセットデータ

配置:

- `src/auspiq/data/facets/facet_1_subject.yaml`
- `src/auspiq/data/facets/facet_2_place.yaml`
- `src/auspiq/data/facets/facet_3_time.yaml`
- `src/auspiq/data/facets/facet_4_type.yaml`

トップレベル:

- `categories`: object 必須

カテゴリノードのキー:

- `title`: string または欠落
- `name`: string または欠落
- `including`: 任意
- `usage_note`: 任意
- `scope_note`: 任意
- `references`: 任意
- `subcategories`: object 必須

必須条件:

- 各ノードは `subcategories` を必ず持ちます。
- leaf でも `subcategories: {}` が必要です。
- ノードは表示名として `title` または `name` のどちらかを持つことが期待されます。
- 実際の分類コードは YAML の mapping key です。ノード内部のフィールドではありません。

実行時の解釈:

- 表示名は `title` があればそれ、なければ `name` を使います。
- selectable node は `label = title or name` を持つノードです。
- facet 名として受理されるのは `subject`、`place`、`time`、`type` の 4 つです。
- コード文字列の書式自体は facet ごとに自由ですが、weight data や generated output と整合している必要があります。

## 重みデータ

配置:

- `src/auspiq/data/weights/stage_{n}_single_weights.json`
- `src/auspiq/data/weights/stage_{n}_double_weights.json`
- `src/auspiq/data/weights/stage_{n}_triple_weights.json`
- schema: `src/auspiq/data/schemas/`

トップレベルキー:

- `schema_version`: string 必須。`x.y.z` の semantic version でなければなりません。
- `data_version`: string
- `stage`: integer
- `weight_type`: string
- `base_weight`: number `0.0..1.0`
- `metadata`: object
- `weights`: non-empty array 必須

追加制約:

- JSON schema に通る必要があります。
- schema fallback validator でも top-level は object 必須、`weights` は空でない配列必須です。

`weights[]` entry のキー:

- `weight_id`: non-empty string 必須
- `weight_type`: `single|double|triple`
- `stage`: integer `0..5`
- `conditions`: array
- `weight_value`: number `0.0..1.0`
- `base_weight`: number `0.0..1.0`

`conditions` の制約:

- array 長は `1..3`
- `single` なら要素数はちょうど `1`
- `double` なら要素数はちょうど `2`
- `triple` なら要素数はちょうど `3`

`conditions[]` のキー:

- `facet`: `subject|place|time|type`
- `classification_code`: non-empty string
- `operator`: `equals|contains|starts_with`
- `value`: string または欠落

演算子の意味:

- `equals`
  `classification_code` に対する完全一致です。`classification_code` 側では `*` ワイルドカードを許容します。
- `contains`
  `value` 側の部分一致です。
- `starts_with`
  `value` 側の前方一致です。

`value` の意味:

- `classification_code` ではなく、facet の表示値側に対して評価します。

double / triple 固有の追加設定:

- `select`
  一致 entry が複数あるときの選択戦略です。
- 許可値は `first`、`most_specific`、`max_weight` です。

## 実行時解決

ロード:

- stage ごとに `single`、`double`、`triple` を別ファイルとしてロードします。

優先順:

1. `triple`
2. `double`
3. `single`
4. `base`

各種別の解釈:

- `single`
  一致 entry 群のうち最大 `weight_value` を返します。
- `double`
  一致 entry 群から `select` 戦略で 1 件を選びます。
- `triple`
  一致 entry 群から `select` 戦略で 1 件を選びます。
- `base`
  `default_weight`、データファイルの `base_weight`、内蔵既定値の順に使います。

`most_specific` の比較:

- operator score は `equals=3`、`starts_with=2`、`contains=1`
- `classification_code` の `*` 数は少ない方が優先
- 同点時は `weight_value` を比較
