# 開発ガイド

AuspiQの開発に関する情報をまとめています。

## プロジェクト構造

```text
src/
├── auspiq/
│   ├── __init__.py
│   ├── cli.py                    # メインCLIエントリーポイント
│   ├── config.py                 # 設定管理システム
│   └── commands/
│       ├── __init__.py
│       └── config.py             # 設定関連のCLIコマンド
tests/
├── __init__.py
├── test_config.py                # 設定システムのテスト
└── test_config_commands.py       # 設定コマンドのテスト
docs/
├── user/
│   ├── installation.md          # インストールガイド
│   └── configuration.md         # 設定システムの使用方法
└── developer/
    ├── development.md            # 開発ガイド（このファイル）
    ├── api-reference.md          # API リファレンス
    └── contributing.md           # コントリビューションガイド
```

## 開発環境のセットアップ

### 前提条件

- Python 3.13+
- Poetry または pip

### セットアップ手順

1. リポジトリをクローン：

   ```bash
   git clone <repository-url>
   cd auspiq_quiz_trainer
   ```

2. 仮想環境を作成・アクティベート：

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # または
   .venv\Scripts\activate     # Windows
   ```

3. 依存関係をインストール：

   ```bash
   pip install -e .[dev]
   ```

## 実装済み機能

### Phase 1.2: 設定システム

#### 設定管理 (`src/auspiq/config.py`)

- **Config モデル**: Pydantic を使用した設定データの定義
- **ConfigManager クラス**: 設定ファイルの読み書きと管理

主要な機能：

- 設定ファイルの自動作成
- デフォルト値の提供
- JSON 形式での設定保存
- 環境変数からの API キー取得
- 設定値のバリデーション
- キャッシュ機能

#### CLI コマンド (`src/auspiq/commands/config.py`)

- `show`: 設定表示
- `set`: 設定値変更
- `reset`: デフォルトリセット
- `delete`: 設定ファイル削除
- `check`: 設定妥当性チェック

Rich ライブラリを使用した美しい表形式の出力を提供。

#### メイン CLI (`src/auspiq/cli.py`)

Click を使用したコマンドライン インターフェース。

## テスト

### テスト実行

```bash
# 全テスト実行
source .venv/bin/activate && python -m pytest tests/ -v

# 特定のテストファイル実行
source .venv/bin/activate && python -m pytest tests/test_config.py -v

# カバレッジ付きテスト実行
source .venv/bin/activate && python -m pytest tests/ --cov=auspiq --cov-report=html
```

### テスト構成

- **test_config.py**: ConfigManager クラスのユニットテスト（19テスト）
- **test_config_commands.py**: CLI コマンドのテスト（17テスト）

全36テストが実装されており、設定システムの動作を包括的にカバーしています。

## コード品質

### リンティングとフォーマット

```bash
# Black でフォーマット
source .venv/bin/activate && black src/ tests/

# Flake8 でリンティング
source .venv/bin/activate && flake8 src/ tests/

# MyPy で型チェック
source .venv/bin/activate && mypy src/
```

### 設定

- **Black**: `pyproject.toml` で行長88文字、Python 3.13対応
- **MyPy**: 型アノテーション必須、厳格なチェック

## アーキテクチャ設計

### 設計原則

1. **モジュラー設計**: 機能ごとに明確に分離
2. **テスト駆動**: 包括的なユニットテスト
3. **型安全性**: Pydantic と MyPy による型チェック
4. **ユーザビリティ**: Rich による美しい CLI 出力

### データフロー

```text
CLI Command → ConfigManager → JSON File
     ↓              ↑
  Rich Output ← Config Model
```

### エラーハンドリング

- 設定ファイルの読み書きエラー
- 不正な設定値のバリデーション
- 環境変数の存在チェック
- ファイル権限エラー

## コーディング規約

1. **型アノテーション**: すべての関数に型ヒントを追加
2. **ドキュメント**: クラスと関数に docstring を記述
3. **テスト**: 新機能には対応するテストを追加
4. **エラーハンドリング**: 適切な例外処理を実装

## 参考資料

- [Click Documentation](https://click.palletsprojects.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)
