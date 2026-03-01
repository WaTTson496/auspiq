# コード変更後にドキュメントを更新する

このページは、コード変更を docs に追随させるときの判断基準です。

## 利用者向けドキュメントに反映する変更

- CLI オプションや保存物が変わる
- JSON 入出力契約が変わる
- `predict` / `generate` / `practice` の使い分けが変わる
- トラブルシュート対象が変わる

反映先:

- `docs/end-user/how-to/`
- `docs/end-user/reference/`
- 必要なら `docs/end-user/explanation/`

## 開発者向けドキュメントに反映する変更

- module 責務や接続が変わる
- facet / weight / prompt / quality / persistence の契約が変わる
- current data gaps が増減する

反映先:

- `docs/developer/reference/`
- `docs/developer/explanation/`
- `docs/developer/policies/`

## 原則

- 手順の変更は how-to
- 仕様の変更は reference
- 判断理由の変更は explanation
- 守るべきルールの変更は policies

AuspiQ では docs 追随の漏れがそのまま暗黙契約の増加につながります。特に generation 周りは、実装、データ、保存物のどこが authoritative source なのかが曖昧になりやすいので、変更時に docs を後回しにしないことが重要です。
