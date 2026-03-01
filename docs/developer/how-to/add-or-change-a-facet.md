# ファセットを追加・変更する

このページは、facet YAML を追加または変更するときの作業手順です。

## 触る場所

- `src/auspiq/data/facets/`
- `src/auspiq/facet_manager.py`
- 必要なら `src/auspiq/question_prompt.py`
- 必要なら weight data

## 手順

1. 対象 facet の YAML を編集します。
2. 各 category に `title` または `name`、`subcategories` があることを確認します。
3. leaf ノードにも `subcategories: {}` を入れます。
4. 変更した code を参照する weight data や candidate map が壊れていないか確認します。
5. prompt で使われる表示名や hierarchy が意図通りか確認します。

## 壊れやすい場所

- `candidate_map` の code
- weight data の conditions
- `facet_labels` と prompt 上の表示
- quality validator の `facet.unknown`

## ドキュメント反映

- end-user reference の生成仕様
- developer reference の facet/weight 契約
- current data gaps に追加が必要か

facet 変更は見た目以上に広い作業です。YAML が読めるだけでは不十分で、prompt 上の表現、weight data の条件一致、quality validator の code 存在確認まで一通り影響します。
