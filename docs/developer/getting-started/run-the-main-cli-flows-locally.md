# 基本 CLI フローをローカルで動かす

このページは、end-user 向けの基本フローをローカルで一通り触り、どのコマンドが何を出すかを掴むためのものです。

## 1. 設定を確認する

```bash
auspiq config show
auspiq config check
```

## 2. 解析を触る

```bash
auspiq predict single "静岡県と山梨県の県境に位置する、標高/"
auspiq predict full "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？" "富士山"
```

見るもの:

- `results/auspiq_single_*.json`
- `results/auspiq_full_*.json`
- 単発推測と全文解析で保存形式が違うこと

## 3. 生成を触る

```bash
auspiq generate --format json --output generated.json
auspiq generate --count 3 --parallelism 2 --format json --output generated-batch.json
```

見るもの:

- 単発 JSON の `quality_report` と `selection`
- `facet_labels`
- `weight_selection`
- `metadata`
- 複数生成の `summary` / `results` / `failures`
- `~/.auspiq-jobs.json`
- `--output` を付けない限り保存されないこと

## 4. 練習を触る

```bash
auspiq practice --file generated.json --feedback-out feedback/practice.json
```

見るもの:

- 練習 UI の進行
- 解析結果 JSON と生成結果 JSON のどちらも読めること
- `feedback/practice.json`

## 5. ログを見る

- すべての実行で `logs/auspiq_*.log` が増える
- `generate --no-log-file` だけは例外的にファイル出力を止められる

このページの目的は、機能の正しさを証明することではなく、end-user 向けの基本フローがコードベースのどこへつながるかを体感することです。ここまで終えると、以降の reference を読むときに抽象名だけで迷いにくくなります。
