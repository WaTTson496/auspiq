# 開発者向けドキュメント

AuspiQ を変更、保守、拡張する人のためのドキュメントです。end-user docs とは目的が違うため、ここでは実装作業、内部仕様、設計判断、規範を分けて扱います。

この領域の関心は次の5つです。

- 開発環境を立ち上げる
- 変更作業を進める
- 内部仕様を確認する
- 設計判断の理由を理解する
- 変更時に守るべき規範を確認する

AuspiQ の開発で難しいのは、CLI コードそのものより、code と data の境界が広いことです。生成は `commands/generate.py` だけで完結せず、facet YAML、weight JSON、prompt template、quality validator、runtime artifact の理解を伴います。そのため developer docs でも、単なるファイル一覧ではなく、変更作業の観点から情報を再編しています。

読み始める順序としては、まず getting-started で動作と配置を掴み、その後 how-to で変更作業の入口を見て、必要に応じて reference と explanation を読むのが自然です。policies は、実装の前に一度見ておくと後戻りが減ります。

## いま何をしたいですか

### 開発環境を立ち上げたい

- [getting-started/README.md](./getting-started/README.md)

### 変更作業を進めたい

- [how-to/README.md](./how-to/README.md)

### 内部仕様を確認したい

- [reference/README.md](./reference/README.md)

### 設計判断を理解したい

- [explanation/README.md](./explanation/README.md)

### ルールを確認したい

- [policies/README.md](./policies/README.md)
