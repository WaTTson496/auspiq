# auspiq ドキュメント

OpenAI APIを使用した競技クイズの練習用CLIツール「auspiq」の完全ドキュメントです。

## 利用者向けドキュメント

### 基本的な使い方

- **[インストールガイド](user/installation.md)** - システム要件、インストール手順、初期設定
- **[設定ガイド](user/configuration.md)** - 設定ファイル、全CLIコマンド、APIキー設定、トラブルシューティング
- **[予測機能ガイド](user/prediction.md)** - 単発推測、全文解析、一括処理の詳細な使用方法
- **[練習機能ガイド](user/practice.md)** - 対戦形式の早押し練習モードの使い方

### 高度な使い方

- **[バッチAPI活用ガイド](user/batch-api.md)** - コスト効率の良いバッチ処理の使用方法
- **[ファイル形式ガイド](user/file-formats.md)** - サポートされている入力・出力ファイル形式

## 開発者向けドキュメント

### アーキテクチャ

- **[開発ガイド](developer/development.md)** - 開発環境セットアップ、テスト実行、コントリビューション方法
- **[API リファレンス](developer/api-reference.md)** - 全クラス・メソッドの仕様、プログラマティックな使用方法
- **[OpenAI API 連携](developer/api_integration.md)** - API連携の詳細、プロンプト設計、パフォーマンス最適化

## クイックスタート

はじめてauspiqを使用する方は、以下の順番でドキュメントを読むことをお勧めします：

1. [インストールガイド](user/installation.md) でツールをインストール
2. [設定ガイド](user/configuration.md) でAPIキーを設定
3. [予測機能ガイド](user/prediction.md) で基本的な機能を試す
4. [練習機能ガイド](user/practice.md) で実際に早押し練習を行う

## よくある質問

### Q: 最初に何をすれば良いですか？

A: [インストールガイド](user/installation.md)を参照してインストールし、[設定ガイド](user/configuration.md)でOpenAI APIキーを設定してください。

### Q: エラーが発生しました

A: [設定ガイド](user/configuration.md)のトラブルシューティングセクションを確認してください。

### Q: プログラムから使いたいです

A: [API リファレンス](developer/api-reference.md)でプログラマティックな使用方法を確認してください。

### Q: 新機能を追加したいです

A: [開発ガイド](developer/development.md)を参照してください。

## よく使用するコマンド

### 設定管理

```bash
# 設定確認
auspiq config show

# API キー設定
auspiq config set api-key sk-your-api-key

# 設定チェック
auspiq config check
```

### 予測・解析

```bash
# 単発推測
auspiq predict single "問題文の途中まで"

# 全文解析
auspiq predict full "完全な問題文"

# 一括処理
auspiq batch --input questions.txt
```

### 練習

```bash
# 解析結果で練習
auspiq practice --file results.json
```

## 開発者向けクイックセットアップ

```bash
# リポジトリクローン
git clone <repository-url>
cd auspiq_quiz_trainer

# 開発環境セットアップ
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# テスト実行
python -m pytest tests/ -v
```

## ライセンス

MIT License - 詳細は[LICENSE](../LICENSE)ファイルを参照してください。
