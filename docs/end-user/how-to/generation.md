# 問題を生成する

このガイドは、条件を付けて問題を生成し、結果を保存して後続利用できる形にするための手順をまとめたものです。

## 1. まず 1 問生成する

```bash
auspiq generate --format json --output generated.json
```

成功した状態:

- `question`、`answer`、`question_type` を持つ JSON が保存される
- `quality_report` や `selection` を含む詳細出力が見られる

最初から多くの制約を入れないのは、どの制約が結果に効いたのかを見分けやすくするためです。生成は題材選択、prompt、品質評価が連動するので、いきなり複数軸を変えると原因が追いにくくなります。

## 2. 問題タイプや長さを制約する

```bash
auspiq generate --question-type SC --length-target 90 --length-tolerance 20 --format json --output generated-sc.json
```

使い分け:

- `--question-type SC|OV`: 構文タイプを固定したいとき
- `--length-target`: 目標文字数を指定したいとき
- `--length-tolerance`: 長さの許容幅を狭めたいとき

## 3. 複数問をまとめて生成する

```bash
auspiq generate --count 10 --parallelism 4 --format json --output generated-batch.json
```

成功した状態:

- `summary`、`results`、`failures` を持つ JSON が保存される
- 複数生成時は `~/.auspiq-jobs.json` にジョブ情報が残る

## 4. モードと品質のバランスを変える

```bash
auspiq generate --mode high_quality --format json --output generated-hq.json
```

判断:

- まず既定の `standard` で挙動を見る
- スコア下限や再試行を強めたいときに `high_quality` を使う
- 速度や気軽さを優先するなら、むやみに高品質側へ寄せない

## 5. 設定ファイルで条件をまとめる

`--settings-file` は JSON を読み込みます。

```json
{
  "stage": 0,
  "question_type": "SC",
  "quality": {
    "length_target": 90,
    "length_tolerance": 20,
    "min_score": 70
  },
  "parallelism": 4
}
```

```bash
auspiq generate --settings-file generation-settings.json --count 5 --format json --output generated.json
```

`settings-file` は、繰り返し使う条件セットを固定したいときに向いています。一方で、その場の試行錯誤では CLI オプションの方が差分を追いやすい場面もあります。どちらが正しいというより、再現したいか、試したいかで使い分けます。

## 6. 結果を後で使えるように保存する

- `generate` は `--output` を付けたときだけファイルを書きます
- `practice` に渡すなら JSON で保存します
- 生成理由を追いたいときは `output-level` を既定の `detail` のまま使います
- 複数生成では `failures` も含めて残すと、条件が厳しすぎるかどうかを後で判断しやすくなります

## 関連

- JSON 構造は [../reference/generation.md](../reference/generation.md)
- 生成の考え方は [../explanation/generation.md](../explanation/generation.md)
