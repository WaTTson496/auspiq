# AuspiQ がデータ駆動である理由

AuspiQ の生成は、facet YAML、weight JSON、prompt template、quality rule という複数の data-driven 要素を持っています。これは、生成ロジックのすべてを Python に埋め込まないためです。

この設計の利点は、題材選択や制御ルールをコード変更なしに調整しやすいことです。一方で、契約違反やズレが runtime まで見えにくいという欠点もあります。AuspiQ の保守では、この柔軟性と不安定さの両方を前提に扱う必要があります。

data-driven だからこそ、reference と policies の重要度が高くなります。コードだけを読んでも十分ではなく、YAML、JSON、template の解釈ルールまで含めて documentation されている必要があります。
