# リリースノート

このページは、Diataxis の tutorial / how-to / reference / explanation の外側に置く changelog です。ここでは使い方や内部仕様ではなく、版ごとの変更点だけを記録します。

## 未リリース

### 追加

- `auspiq generate` による問題生成フローを追加
- ファセット選択、重み、品質評価を含む生成パイプラインを追加
- 生成結果を `practice` に入力できるようにした
- OpenAI Batch API を使う `predict batch` のジョブ追跡を追加

### 変更

- 設定ファイル `~/.auspiq.json` に問題生成の既定値を追加
- ローカル保存物として `results/`、`logs/`、`~/.auspiq-jobs.json` を使う構成を明確化した

### 既知の制限

- `generate` のデータ依存部は `src/auspiq/data/facets/` と `src/auspiq/data/weights/` の整合性に依存する
- OpenAI API の応答が JSON 契約を満たさないと生成は失敗する
- SQLite ベースの generated question store は実装されているが、現状の CLI では前面に出ていない
