# パッケージ構成

このページは、`src/auspiq` のモジュール境界を定義するものです。

## CLI / コマンド層

- `cli.py`: ルート CLI とグローバルオプション
- `commands/config.py`
- `commands/predict.py`
- `commands/practice.py`
- `commands/generate.py`

## 実行時設定 / 成果物

- `config.py`: 設定モデルと設定ファイル管理
- `logging_config.py`: ログ初期化
- `file_io.py`: JSON/CSV の入出力
- `batch_manager.py`: ジョブ台帳
- `models.py`: CLI 間 JSON 契約

## 解析 / 練習

- `api_client.py`: OpenAI API 境界
- `prompts.py`: 共通 prompt ローダ
- `practice.py`: 練習エンジン

## 生成

- `generation_settings.py`: 生成設定とモード
- `generation_pipeline.py`: オーケストレーション
- `question_generator.py`: API 応答の生成側パース
- `question_prompt.py`: 生成用 prompt 構築
- `quality_validator.py`: ヒューリスティック品質検証
- `generation_store.py`: SQLite 永続化

## データ駆動コンポーネント

- `facet_manager.py`
- `facet_selector.py`
- `weight_manager.py`
- `weights/`
- `data/facets/`
- `data/weights/`
- `data/schemas/`

実務上は、これらを「コード」と「データ」の二分法で見るより、変更時にどの契約を壊しうるかで見る方が有用です。たとえば prompt template はコードではないものの、JSON 契約や quality の傾向に影響するため、実質的には重要な実装境界です。
