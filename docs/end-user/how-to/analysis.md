# 問題を解析する

このガイドは、問題文を解析して結果を保存し、後で使える形にするための手順をまとめたものです。

## いつ何を使うか

- いま見えている断片から候補を知りたい: `predict single`
- 問題全体のどこで押せそうか見たい: `predict full`
- 複数問をまとめて処理したい: `predict batch`
- 大量処理を非同期で回したい: `predict batch --use-batch-api`

## 1. 1問だけ途中推測する

```bash
auspiq predict single "静岡県と山梨県の県境に位置する、標高/"
```

成功した状態:

- 画面に候補と蓋然性が出る
- `results/auspiq_single_YYYYMMDD_HHMMSS.json` が残る

補足:

- 保存ファイルは常に JSON です。`--format table` は画面表示形式だけを変えます。
- 断片入力そのものに対して応答が返るので、「今この場面で何が有力か」を見たいときに向いています

## 2. 1問を全文解析する

```bash
auspiq predict full "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？" "富士山"
```

成功した状態:

- 位置ごとの解析が進む
- `analysis_points` を持つ JSON が保存される
- 後で `practice` に渡せる

判断:

- `ANSWER` は任意ですが、練習へ流すなら付けて保存します
- `--step` を大きくすると速くなりますが、押し位置の粒度は粗くなります
- `--min-length` を上げると序盤のノイズは減りますが、早い押しどころの観察はしにくくなります

## 3. 複数問をまとめて処理する

入力ファイルは JSON または CSV を使います。どちらも解答が必要です。

```json
[
  {
    "question": "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？",
    "answer": "富士山"
  }
]
```

```bash
auspiq predict batch --input questions.json --mode full
```

成功した状態:

- `results/auspiq_batch_YYYYMMDD_HHMMSS.json` が作られる
- 各問題が `questions` 配列として保存される

注意:

- `--mode single` は `predict single` の繰り返しではありません。各問題の中間地点で1回だけ推測して `AnalysisResult` 形式に包みます。
- そのため、「任意の押しポイントを人間が指定して試す」用途には向きません

## 4. OpenAI Batch API で非同期処理する

```bash
auspiq predict batch --input questions.json --mode full --use-batch-api --submit
```

ジョブ確認:

```bash
auspiq predict batch --list-jobs
auspiq predict batch --status <job-id>
auspiq predict batch --retrieve <job-id>
```

raw 結果も確認したいとき:

```bash
auspiq predict batch --retrieve <job-id> --save-raw-results
```

注意:

- ローカル追跡には `~/.auspiq-jobs.json` を使います
- `--retrieve` は元の入力ファイルを再読込するので、入力ファイルを移動しないでください
- 大量処理で時間短縮やコスト効率を狙うときに向いていますが、その場で結果を確認したい作業には通常の batch の方が扱いやすいです
- `batch` では `--input`、`--status`、`--retrieve`、`--list-jobs` を同時には使えません
- `--use-batch-api` を付けるだけでは処理は始まらず、`--submit` が必要です

## 関連

- 入出力仕様は [../reference/analysis.md](../reference/analysis.md)
- 練習への接続は [practice.md](./practice.md)
