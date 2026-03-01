# 結果を使って練習する

このガイドは、解析結果または生成結果を使って練習し、必要ならフィードバックを保存するための手順をまとめたものです。

## 前提

- `predict full` / `predict batch` の結果 JSON、または `generate` の結果 JSON がある

## 1. 解析結果から練習する

```bash
auspiq practice --file results/auspiq_full_YYYYMMDD_HHMMSS.json
```

成功した状態:

- 問題文が順次表示される
- 閾値を超えた位置で自動停止できる

調整:

- `--threshold`: 自動停止の閾値
- `--speed`: 文字表示速度
- `--start-from`: 何問目から始めるか。0 始まり
- `--limit`: 何問ぶん練習するか

考え方:

- 閾値を上げると、より確信が高い位置まで待つ練習になります
- 閾値を下げると、早めに押す感覚を試しやすくなります
- 表示速度は、判断速度を鍛えたいのか、問題理解を優先したいのかで変えます

## 2. 生成結果から練習する

```bash
auspiq practice --file generated.json
```

注意:

- 生成結果は読めますが `analysis_points` を持たないため、解析結果と同じ自動停止は起きません
- 練習体験を自分で刻みたいときに向いています
- 同じ `threshold` を指定しても、解析結果ベースほど意味を持ちません

## 3. フィードバックを保存する

```bash
auspiq practice --file generated.json --feedback-out feedback/practice.json
```

保存される内容:

- セッション全体の `summary`
- 問題ごとの `result`
- `push_position`
- `time_taken`
- 入力元メタデータ

これを残しておくと、「どの種類の問題で遅れやすいか」「生成結果ベースと解析結果ベースで体験がどう違ったか」を後から見返せます。

## 4. 練習の途中操作を確認する

- Enter: 状態によって、一時停止、解答権獲得、解答入力への移行、再開のいずれか
- `c`: 解答権獲得後に問題文表示を継続
- `a`: 解答表示
- `n`: 次の問題
- `q`: 練習終了

補足:

- 自動停止が起きた場合は、システムが解答権を獲得します
- その状態で Enter を押すと解答入力処理へ進みます

## 関連

- 入力形式の正確な仕様は [../reference/practice.md](../reference/practice.md)
- 入力元ごとの向き不向きは [../explanation/practice.md](../explanation/practice.md)
