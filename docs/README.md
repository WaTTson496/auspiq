# AuspiQ ドキュメント

AuspiQ は、競技クイズの問題を解析し、問題を生成し、その結果を使って早押し練習を行うための CLI ツールです。

このドキュメントは、まず読む人の立場で 2 系統に分かれています。最初に選ぶのは文書種別ではなく、AuspiQ を使う人か、AuspiQ を変更する人かです。

AuspiQ の特徴は、単一の対話的ツールというより、複数の CLI ワークフローとその保存物から成ることにあります。`predict` は解析結果を JSON に残し、`generate` は生成結果と品質情報を残し、`practice` はそれらを入力として練習体験を作ります。したがって docs でも、コマンド一覧ではなく、「どの立場の人が、どの目的で、どの情報を見に来るか」を起点に構成しています。

このトップページでやることは 3 つだけです。

- AuspiQ が何をするツールかを短く理解する
- 自分が end-user と developer のどちらかを選ぶ
- release notes のような補助資料へ入る

## あなたはどちらですか

### AuspiQ を使う人

`predict`、`generate`、`practice` を使って作業を進める人向けです。end-user docs では、まず「初めて使う」「作業を完了したい」「仕様を確認したい」「背景を理解したい」の4種類の必要を分けて案内します。

- 初めて使う
- 目的の作業を完了したい
- 設定や JSON 仕様を確認したい
- 解析・生成・練習の使い分けを理解したい

入口: [end-user/README.md](./end-user/README.md)

end-user docs で扱う中心主題は次の 3 本柱です。

- 問題を解析する
- 問題を生成する
- 解析結果や生成結果を使って練習する

ただし、設定、ログ、保存物、JSON 形式、トラブル対応はこの 3 本柱を横断する主題として独立に扱います。

### AuspiQ を開発・拡張する人

CLI、内部モジュール、facet / weight / prompt / quality の契約、開発ルールを確認したい人向けです。developer docs では、環境構築、変更作業、内部仕様、設計判断、規範を分けて扱います。

- 開発環境を立ち上げる
- コマンドやデータを変更する
- 内部仕様を確認する
- 設計判断や規範を確認する

入口: [developer/README.md](./developer/README.md)

developer docs で特に重要なのは、AuspiQ が data-driven な部分を多く持つことです。生成は code だけでなく facet YAML、weight JSON、prompt template、quality validator の組合せで振る舞います。そのため、内部仕様と変更手順、設計理由、規範を別々に読める構造にしています。

## 補助資料

- [appendix/release-notes.md](./appendix/release-notes.md)
- [appendix/docs-meta.md](./appendix/docs-meta.md)
- [appendix/known-gaps.md](./appendix/known-gaps.md)
