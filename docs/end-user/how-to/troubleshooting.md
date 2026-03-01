# トラブルシューティング

このガイドは、よくある失敗を症状から切り分けるためのものです。

## API キー関連で失敗する

確認:

```bash
auspiq config show
auspiq config check
```

見るところ:

- 設定ファイルの `api_key` が空でないか
- `~/.auspiq.json` 以外を使っているなら `--config-file` が合っているか

注意:

- `OPENAI_API_KEY` は `config show/check` では見えますが、実行系コマンドは設定ファイル側の `api_key` を前提にしています

そのため、「show では見えているのに実行は失敗する」という症状が起こりえます。まず設定ファイルへ保存されているかを確認してください。

## `practice` が入力を読めない

確認:

- JSON 以外を渡していないか
- `predict full` / `predict batch` の結果か
- `generate` の単発またはバッチ結果か

注意:

- ただの JSON 配列や CSV は読めません
- 解析結果を使うなら各問題に解答が必要です

よくある誤りは、`predict single` の出力をそのまま `practice` に渡すことです。`practice` が読めるのは解析結果全体か生成結果であり、単発推測レスポンスではありません。

## `predict batch --retrieve` が失敗する

確認:

- `~/.auspiq-jobs.json` に対象ジョブが残っているか
- 登録時に使った入力ファイルがまだ同じ場所にあるか

## 期待した場所にファイルがない

確認:

- `predict` 系は既定で `results/`
- ログは `logs/`
- `generate` は `--output` を付けないと保存しない
- `practice` のフィードバックは `--feedback-out` を付けないと保存しない

## 品質スコアが低い

確認:

- 長さ制約が厳しすぎないか
- `question_type` の指定が実際の文とズレていないか
- `high_quality` モードや `settings-file` で `min_score` を調整した結果、通過条件が上がりすぎていないか

品質スコアは絶対的な良し悪しではなく、ヒューリスティックな目安です。特に length や question type のズレは warning として積み上がるので、まず `issues` の内訳を見て、何が下げているかを確認します。

## まず見るべきもの

- `logs/auspiq_YYYYMMDD_HHMMSS.log`
- `config show`
- 保存された JSON 本体
