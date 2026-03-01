# 既知のギャップ

このページは、reader type を問わず影響しうる既知のズレや注意点の入口です。詳細な内部事情は developer reference にありますが、docs 全体として見失いやすい点をここにまとめます。

## 既知のギャップ一覧

- `generate` には SQLite store 実装がありますが、通常の CLI 経路では未接続です
- prompt 実装は prediction 系と generation 系で分かれており、同じ template 体系ではありません
- `facet_3_time.yaml` には parser 契約と食い違う `children` キーが残っています
- quality report は semantic truth を保証しません

## 詳細

- 内部契約としての詳細は [../developer/reference/current-data-gaps.md](../developer/reference/current-data-gaps.md)
