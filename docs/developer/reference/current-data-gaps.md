# 現状のデータギャップ

このページは、現行コードベースで見えているズレや曖昧さを記録するものです。

## 現在確認できるギャップ

### `GeneratedQuestionStore` は存在するが、通常の `generate` CLI では未接続

実装側には SQLite へ保存する仕組みがありますが、通常の CLI 経路では pipeline 生成時に store を注入していません。そのため、「コード上はある保存先」と「普段の運用で実際に使われる保存先」がずれています。

### prompt 実装は prediction 系と generation 系で分かれているが、共通 README だけでは差が見えにくい

`PromptTemplate` の共通 loader と、`QuestionPromptBuilder` ベースの生成 prompt は責務が違います。docs でこの差を曖昧にすると、「どのテンプレートを変えると何に効くのか」が分からなくなります。

### weight schema では top-level と entry の両方に `base_weight` がある一方、runtime の fallback 意味は主に single data に寄っている

schema 上は柔軟ですが、runtime の解決順と fallback は単純な対称構造ではありません。schema の見た目だけで意味を推測すると誤読しやすい箇所です。

### facet YAML には外部 schema がなく、契約検証は runtime parser に依存している

これは、契約違反が静的には見えにくく、実行時に初めて分かることを意味します。facet data の保守では大きな不安定要因です。

具体例として、`facet_3_time.yaml` には `subcategories` ではなく `children` を使っている箇所が残っています。現行 parser は `subcategories` しか読まないため、これは一般論ではなく、実際の runtime 契約違反です。

### `candidate_map` は正規化されるが、facet 名や code の事前妥当性検証がない

誤った指定でも早い段階では落ちず、実際の選択時に遅れて問題化します。設定ファイルの再利用や共有を考えると、この遅延エラーは保守上の負債です。

### quality validator は facet code の存在確認までで、意味的一貫性は見ない

quality report があるからといって、生成物が facet 交点に本当に属するとは限りません。ここは LLM と人間のレビューに委ねられています。

### generation の batch job 記録は prediction 用 `BatchJobInfo` を流用している

そのため、一部フィールドは generation では意味が薄いまま残っています。job 管理の抽象が prediction 起点で設計されていることの痕跡です。
