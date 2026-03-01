# 最初の生成

このレッスンでは、AuspiQ で 1 問生成し、生成結果 JSON を確認するところまで進めます。ここでは条件を増やしすぎず、生成結果がどのような保存物として残るかを確認します。

## 前提

- [first-analysis.md](./first-analysis.md) の前提を満たしている

## 1. まず 1 問生成する

```bash
auspiq generate --format json --output generated.json
```

ここで見るもの:

- `question`、`answer`、`question_type` が返ること
- `generated.json` が保存されること
- `generate` は `--output` を付けたときだけファイルに保存されること

## 2. 制約を 1 つだけ加える

```bash
auspiq generate --question-type SC --length-target 90 --format json --output generated-sc.json
```

ここで見るもの:

- `question_type` を固定できること
- 問題文の長さ目標を与えられること
- 制約は少しずつ足した方が挙動を追いやすいこと

## 3. 詳細出力を確認する

既定の `output-level` は `detail` です。JSON には次のような補助情報も含まれます。

- `facet_codes`
- `facet_labels`
- `quality_report`
- `selection`
- `weight_selection`
- `metadata`

これらは「なぜその問題が出たか」を後から追うための情報です。

ここで重要なのは、AuspiQ の生成が「ただ 1 問返す」だけではないという点です。どのファセットが選ばれたか、どの重み情報が効いたか、品質上どんな警告が出ているかを一緒に残すことで、生成結果を比較したり、後から条件調整したりしやすくしています。

いまの段階では、`mode`、`stage`、`settings-file`、`facet-weight` といった細かい制御には深入りしません。まずは「生成物そのもの」と「生成理由の補助情報」がセットで残ることを理解できれば十分です。

## 4. このレッスンで得たもの

- `generate` は問題文と解答だけでなく、品質評価や選択情報も返す
- 単発生成でも JSON を保存しておくと、後で `practice` に回せる
- 制約は少しずつ追加した方が挙動を理解しやすい

次のレッスンでは、この生成結果や解析結果を実際に `practice` へ渡し、AuspiQ が個別コマンドの集合ではなく、保存物をつなぐワークフローであることを確かめます。
