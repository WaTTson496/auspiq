# 失敗モード

このページは、AuspiQ で表面化する例外と失敗フェーズを列挙するものです。

## 設定・入力系

### `GenerationSettingsError`

- 発生層: settings 正規化、config defaults 適用、CLI override 適用
- 再試行: なし
- 確認先: config 値、`--settings-file`

### `click.ClickException`

- 発生層: CLI 引数検証
- 例:
  - `mode` と `quality` の不一致
  - `batch-size` を単発生成に指定
  - `stage < 0`
  - `settings-file` 読み込み失敗
- 再試行: 入力修正後

### `FileIOError`

- 発生層: `predict batch` の入力読込、解析結果書き出し
- 例:
  - 未対応拡張子
  - JSON/CSV 不正
  - `answer` 欠落
- 再試行: 入力修正後

## データ読込系

### `FacetDataValidationError` / `FacetDataIOError`

- 発生層: facet YAML load / parse
- 再試行: なし
- 確認先: `src/auspiq/data/facets/`、logs

### `WeightDataValidationError` / `WeightDataIOError`

- 発生層: weight JSON load / schema validate
- 再試行: なし
- 確認先: `src/auspiq/data/weights/`、schema

## API / 生成系

### `APIError`

- 発生層: OpenAI API 呼び出し全般
- 利用コマンド: `predict`、`generate`
- 再試行: 呼び出し元依存

### `BatchAPIError`

- 発生層: OpenAI Batch API の submit / status / retrieve
- 利用コマンド: `predict batch`
- 再試行: 状況依存

### `QuestionGenerationAPIError`

- 発生層: `generate` の API call
- 再試行: あり。認証系エラー以外で generator の retry 対象になることがあります。
- 確認先: API キー、モデル、logs

### `QuestionGenerationValidationError`

- 発生層: API 応答 JSON parse
- 再試行: なし
- 確認先: prompt、response format、logs

### `QualityValidationError`

- 発生層: quality validator 自体の異常
- 再試行: なし
- 確認先: generated payload、quality settings

### `GenerationStoreError`

- 発生層: SQLite 永続化
- 再試行: なし
- 確認先: DB path、schema、filesystem permission

## パイプライン系

### `GenerationPipelineError`

- 発生層: pipeline phase wrapper
- `phase` の値:
  - `facet_selection`
  - `prompt_generation`
  - `api_call`
  - `quality_validation`
  - `batch`
  - `store`
- 再試行: phase 自体ではなく下位層依存
- 確認先: `phase`、detail JSON、logs
