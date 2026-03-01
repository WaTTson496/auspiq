# 生成がパイプラインである理由

生成を pipeline として分けている理由は、題材選択、prompt 構築、API 呼び出し、品質検証、保存を一つの巨大関数にしないためです。

この分割にすると、失敗した場所を phase で切り分けやすくなります。実際、`GenerationPipelineError` には phase が入り、facet selection で失敗したのか、prompt generation で失敗したのか、quality validation で落ちたのかを区別できます。

また、複数生成では単発生成の繰り返しを並列化して進捗だけ別に集約できます。pipeline で単発の責務を固定しておくと、batch でも単発と同じ意味の結果を扱いやすくなります。metadata に prompt、selection、timings を残しているのも、段階構造があるからです。

pipeline 化には、どこまでが deterministic で、どこからが probabilistic かを分けやすいという利点もあります。facet selection や weight resolution はデータと設定に依存する比較的説明しやすい層で、API call 以降は LLM の揺らぎを含みます。層を分けておくことで、挙動の揺れをすべて同じ箱に入れずに済みます。

また、保存や観測の観点でも pipeline は有利です。prompt、selection、timings、quality report を metadata として残せるのは、途中段階が明示されているからです。AuspiQ の生成が比較や調整に向くのは、単に多機能だからではなく、段階ごとの観測点を持っているからです。
