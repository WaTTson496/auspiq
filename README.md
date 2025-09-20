# AuspiQ

OpenAI APIを使用した競技クイズの練習用CLIツールです。

## 概要

AuspiQは、AIを使って早押しクイズの問題文の続きを予測し、解答候補を提示するCLIアプリケーションです。

## 主要機能

### AI予測機能

- **単発推測**: 問題文の途中から続きと解答候補を予測
- **全文解析**: 問題文全体を解析して各位置での推測精度を分析
- **一括処理**: ファイルから複数問題を読み込んで一括処理
- **バッチAPI対応**: OpenAI Batch APIによる非同期処理

### 練習機能

- **対戦システム**: プレイヤーvsAIシステムの対戦形式
- **解答権システム**: 早押しによる解答権獲得と実際の解答入力
- **スコア管理**: 正解・不正解の記録とリアルタイムスコア表示
- **自動停止**: 高確信度位置でAIが解答権獲得
- **リアルタイム表示**: 文字の順次表示
- **複数問題対応**: 連続して複数問題を練習可能

### 設定・管理機能

- **設定管理**: OpenAI APIキーやモデル設定の管理
- **CLI インターフェース**: コマンドライン インターフェース
- **設定ファイル**: `~/.auspiq.json` による設定の永続化
- **環境変数対応**: `OPENAI_API_KEY` 環境変数の自動検出
- **設定バリデーション**: 設定値の妥当性チェック

### ファイル対応

- **複数入力形式**: テキスト、CSV、JSON形式をサポート
- **結果出力**: JSON形式での詳細な解析結果
- **練習ファイル**: 解析結果を練習用に変換

## クイックスタート

### インストール

```bash
pip install -e .
```

### 基本的な使用方法

1. OpenAI APIキーを設定:

   ```bash
   auspiq config set api-key YOUR_API_KEY
   ```

2. 設定を確認:

   ```bash
   auspiq config show
   ```

3. 設定の妥当性をチェック:

   ```bash
   auspiq config check
   ```

### 基本的な使用例

```bash
# 1. 単発推測 - 問題文の途中から続きを予測
auspiq predict single "静岡県と山梨県の県境に位置する、標高"

# 2. 全文解析 - 問題全体の各位置での推測精度を分析
auspiq predict full "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？"

# 3. 一括処理 - ファイルから複数問題を処理
auspiq batch --input questions.txt

# 4. バッチAPI - 50%コスト削減で大量処理
auspiq batch --input questions.txt --use-batch-api --submit

# 5. 練習モード - プレイヤーvsAIの対戦形式練習
auspiq practice --file results.json --threshold 80 --speed 0.1

# 設定管理
auspiq config set api-key sk-your-api-key
auspiq config show
auspiq config check
```

## ドキュメント

### 利用者向け

- **[インストールガイド](docs/user/installation.md)** - システム要件、インストール手順、初期設定
- **[設定ガイド](docs/user/configuration.md)** - 設定ファイル、全CLIコマンド、APIキー設定、トラブルシューティング
- **[予測機能ガイド](docs/user/prediction.md)** - 単発推測、全文解析、一括処理の詳細な使用方法
- **[練習機能ガイド](docs/user/practice.md)** - 対戦形式の早押し練習モードの使い方
- **[バッチAPI活用ガイド](docs/user/batch-api.md)** - バッチ処理の使用方法
- **[ファイル形式ガイド](docs/user/file-formats.md)** - サポートされている入力・出力ファイル形式

### 開発者向け

- **[開発ガイド](docs/developer/development.md)** - 開発環境セットアップ、テスト実行、コントリビューション方法
- **[API リファレンス](docs/developer/api-reference.md)** - 全クラス・メソッドの仕様、プログラマティックな使用方法
- **[OpenAI API 連携](docs/developer/api_integration.md)** - API連携の詳細、プロンプト設計、パフォーマンス最適化

**すべてのドキュメント**: [ドキュメント一覧](docs/README.md)

## より詳しい使い方

### 機能別ガイド

- **予測機能の詳細**: [予測機能ガイド](docs/user/prediction.md) - 単発推測から一括処理まで
- **練習機能の詳細**: [練習機能ガイド](docs/user/practice.md) - 対戦形式の早押し練習の使い方
- **バッチAPI活用**: [バッチAPI活用ガイド](docs/user/batch-api.md) - バッチ処理
- **ファイル形式**: [ファイル形式ガイド](docs/user/file-formats.md) - 入出力ファイルの詳細仕様

### 困ったときは

- **インストールで困った場合**: [インストールガイド](docs/user/installation.md) のトラブルシューティング
- **設定の詳細**: [設定ガイド](docs/user/configuration.md) または `auspiq config --help`
- **プログラムから使用したい場合**: [API リファレンス](docs/developer/api-reference.md)
- **開発に参加したい場合**: [開発ガイド](docs/developer/development.md)

## ライセンス

MIT License

## 名前の由来

「AuspiQ」の名前の由来は、ラテン語の「auspex」（卜占官）とQuizの「Q」を合成したものです。auspexは古代ローマにおいて鳥の飛び方などから未来を占う役職で、早押しクイズにおいて、問題文の途中までの情報から先の展開や答えを見通すようなイメージから名付けました。
