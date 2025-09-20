# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリでコードを作業する際のガイダンスを提供します。

ローカルの設定: @_tmp/CLAUDE.md

## プロジェクト概要

これは「AuspiQ」プロジェクトです。OpenAI APIを活用した競技クイズのトレーニングツールで、CLIアプリケーションとして実装されています。

## 現在の状態

- Python 3.13プロジェクト
- pyproject.tomlで依存関係管理
- srcディレクトリにauspiqパッケージが配置
- Click、OpenAI、Rich、Pydanticなどのライブラリを使用
- CLIエントリーポイント: `auspiq`
- 開発用ツール: pytest, black, flake8, mypy

## 開発セットアップ

### 使用技術

- プログラミング言語: Python 3.13
- パッケージマネージャー: pip (pyproject.toml)
- CLIフレームワーク: Click
- AI API: OpenAI
- UI: Rich
- データ検証: Pydantic

### ビルド・テストツール

- テスト: pytest
- フォーマッター: black
- リンター: flake8
- 型チェック: mypy

### 実行方法

```bash
# パッケージインストール（開発モード）
pip install -e .

# CLIツール実行
auspiq

# テスト実行
pytest

# コード品質チェック
black .
flake8 .
mypy .
```

## アーキテクチャ

競技クイズ（早押しクイズ）のトレーニングを支援するCLIアプリケーション。OpenAI APIを使用して問題の予測や解答支援を行う機能を提供しています。

### 主要モジュール

- `cli.py`: CLIエントリーポイント
- `api_client.py`: OpenAI API連携
- `models.py`: データモデル定義
- `config.py`: 設定管理
- `practice.py`: 練習機能
- `batch_manager.py`: バッチ処理管理
- `prompts.py`: プロンプト管理

## 注意事項

- markdownを書くときはmarkdownlintのルールに従う
- ファイルの末尾には必ず改行を入れる
- Python 3.13の機能を活用する
- 型ヒントを必須とする（mypy設定により）
- Blackのフォーマットに従う（line-length: 88）
