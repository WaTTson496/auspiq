# コマンドと内部実装の接続

このページは、CLI から core module への接続をまとめたものです。

## ルート CLI

- `cli.py` が `config`、`generate`、`predict`、`practice` を登録する
- `analyze` は `predict full` のエイリアス
- `batch` は `predict batch` のエイリアス

## `config`

- `commands/config.py`
- `ConfigManager` と `OpenAIClient` の検証機能を使う

## `predict`

- `commands/predict.py`
- `ConfigManager` で設定を読み、`OpenAIClient` を作る
- ファイル入力は `QuestionLoader`
- バッチ管理は `BatchJobManager`
- 出力保存は `ResultWriter`

## `practice`

- `commands/practice.py`
- 入力 JSON は `models.py` の Pydantic モデルで判別する
- 実行本体は `PracticeEngine`

## `generate`

- `commands/generate.py`
- `ConfigManager` で既定値を読み、`GenerationSettings` へ畳み込む
- `FacetManager`、`WeightManager`、`QuestionPromptBuilder`、`OpenAIClient`、`QuestionGenerator` を束ねて `QuestionGenerationPipeline` を作る
- 複数生成では `BatchJobManager` も使う

開発上の含意:

- `predict` の変更は command 層で完結しやすいが、`generate` は pipeline と data 契約まで見た方がよい
- `practice` は入力 JSON 契約への依存が強いので、他コマンド側の出力変更でも影響を受ける
