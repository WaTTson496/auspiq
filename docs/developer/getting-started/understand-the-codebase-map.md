# コードベースの地図を把握する

このページは、AuspiQ のモジュール境界を掴むための地図です。

## CLI とコマンド層

- `src/auspiq/cli.py`
- `src/auspiq/commands/config.py`
- `src/auspiq/commands/predict.py`
- `src/auspiq/commands/practice.py`
- `src/auspiq/commands/generate.py`

## 実行時設定と保存物

- `src/auspiq/config.py`
- `src/auspiq/logging_config.py`
- `src/auspiq/file_io.py`
- `src/auspiq/batch_manager.py`
- `src/auspiq/models.py`

## 解析 / 練習

- `src/auspiq/api_client.py`
- `src/auspiq/prompts.py`
- `src/auspiq/practice.py`

## 生成

- `src/auspiq/generation_settings.py`
- `src/auspiq/generation_pipeline.py`
- `src/auspiq/question_generator.py`
- `src/auspiq/question_prompt.py`
- `src/auspiq/quality_validator.py`
- `src/auspiq/generation_store.py`

## データ駆動部分

- `src/auspiq/facet_manager.py`
- `src/auspiq/facet_selector.py`
- `src/auspiq/weight_manager.py`
- `src/auspiq/weights/`
- `src/auspiq/data/facets/`
- `src/auspiq/data/weights/`
- `src/auspiq/data/schemas/`

## 読み進め方

- 入口を知りたいときは CLI / commands
- 生成を追いたいときは `commands/generate.py` から `generation_pipeline.py`
- データ契約を見たいときは `facet_manager.py`、`weight_manager.py`、`data/schemas/`

注意したいのは、AuspiQ の構造が完全に対称ではないことです。`predict` は command 層が比較的厚く、`generate` は core 側へ責務が分かれています。したがって、「commands 配下を見れば全機能が同じ粒度で理解できる」とは思わない方がよいです。
