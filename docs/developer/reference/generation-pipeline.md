# 生成パイプライン

このページは、`QuestionGenerationPipeline` の段階構造を定義するものです。

## 依存オブジェクト

- `FacetManager`
- `WeightManager`
- `QuestionPromptBuilder`
- `QuestionGenerator`
- 任意で `GeneratedQuestionStore`

## 単発生成の段階

1. `facet_selection`
2. `prompt_generation`
3. `api_call`
4. `quality_validation`
5. `weight_selection`
6. `metadata assembly`
7. 任意で `save`

## ファセット選択

- `FacetCombinationSelector` が `FACET_ORDER` に従って順次選ぶ
- 各段階で、部分的に選ばれた target に対する final weight を候補重みに使う
- `candidate_map` と `leaf_only` がここへ効く

ここでの重要点は、4 軸同時最適化ではなく逐次選択だということです。したがって、ある facet の候補絞りが後続の facet 選択空間に影響します。

## プロンプト生成

- system prompt は `PromptTemplate.get_system_prompt()`
- user prompt は `QuestionPromptBuilder.build_prompt()`
- facet context、question type hint、relation hint、difficulty hint、output schema を埋め込む

## API 呼び出し

- `QuestionGenerator.generate_from_messages()`
- `response_format={"type":"json_object"}`
- 返答 JSON から `question`、`answer`、`question_type` を厳密に抽出する

## 品質検証

- `evaluate_question_quality()`
- `quality_min_score` があればここで落とす

quality validation は semantic truth の保証ではなく、ヒューリスティックな整形と危険信号の検出です。

## 重み選択

- 生成後に `WeightManager.calculate_weight()` を呼び、選ばれた facet 組合せの weight 情報を metadata に残す

## 複数生成

- `ThreadPoolExecutor` で単発生成を並列化する
- 結果は `BatchGenerationResult`
- 進捗は `BatchProgress`

batch は別系統の実装ではなく、単発生成の反復を並列に束ねたものです。そのため、単発で壊れる条件は batch でも基本的に同じです。
