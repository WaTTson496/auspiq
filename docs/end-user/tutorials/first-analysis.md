# 最初の解析

このレッスンでは、AuspiQ で 1 問を解析し、保存された JSON を確認するところまで進めます。目的は `predict single` と `predict full` の違いを体験として掴むことです。

## 前提

- Python 3.13 以上
- リポジトリ取得済み
- `pip install -e .` 済み
- OpenAI API キーを持っている

## 1. API キーを設定する

```bash
auspiq config set api-key sk-...
auspiq config show
```

`config show` で `API Key` が未設定でなければ準備完了です。実行系コマンドは設定ファイル上の `api_key` を参照するので、まず `config set` で保存しておく前提で進めます。

## 2. 途中までの問題文を推測する

```bash
auspiq predict single "静岡県と山梨県の県境に位置する、標高/"
```

ここで見るもの:

- 候補が複数返ること
- 蓋然性が表示されること
- 実行後に `results/auspiq_single_YYYYMMDD_HHMMSS.json` が作られること
- 保存ファイルは `--format table` のままでも JSON であること

## 3. 全文解析を実行する

```bash
auspiq predict full "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？" "富士山"
```

ここで見るもの:

- 途中位置ごとに解析が進むこと
- 押しポイントごとに候補と蓋然性が変わること
- `results/auspiq_full_YYYYMMDD_HHMMSS.json` が作られること
- `ANSWER` を付けて保存すると、後で `practice` に流せること

## 4. 保存物を確認する

生成された JSON を開くと、`questions` の中に `question` と `analysis_points` を持つ構造になっています。ここで確認したいのは、AuspiQ が「画面表示だけのツール」ではなく、後続作業に渡せる保存物を作るツールだという点です。

特に `analysis_points` は、単なるログではなく、各位置でどんな候補がどの程度有力だったかを残すためのものです。`practice` が解析結果を入力として使えるのは、この位置情報があるからです。

また、`predict single` と `predict full` の保存物は形が違います。前者は 1 回の推測応答で、後者は問題全体を通した解析結果です。同じ「予測」でも、後で何に使うかが違うため、保存形式も分かれています。

## 5. このレッスンで得たもの

- `predict single` は「今この断片から何が言えそうか」を見るためのコマンド
- `predict full` は「どの位置で押せそうか」を見るためのコマンド
- 解析結果は画面表示だけでなく JSON として保存され、後続の練習に使える

この段階では、`--step`、`--min-length`、`predict batch` のような派生操作には踏み込みません。次に必要になるのは、「1 問の解析が分かった上で、別の種類の保存物として生成結果を見ること」です。
