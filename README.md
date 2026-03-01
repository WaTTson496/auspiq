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

- **入力形式**: 直接入力（CLI引数） / JSON / CSV
- **結果出力**: JSON 形式の解析結果と統計テキスト
- **練習ファイル**: 解析結果・生成結果の両方に対応

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
auspiq batch --input questions.json

# 4. バッチAPI - 非同期で大量処理
auspiq batch --input questions.json --use-batch-api --submit

# 5. 練習モード - プレイヤーvsAIの対戦形式練習
auspiq practice --file results.json --threshold 80 --speed 0.1

# 設定管理
auspiq config set api-key sk-your-api-key
auspiq config show
auspiq config check
```

## ドキュメント

AuspiQ のドキュメントは Diátaxis に沿って整理しています。

**ドキュメント一覧**: [docs/README.md](docs/README.md)

### チュートリアル

- [クイックスタート](docs/tutorials/quickstart.md)
- [初めての問題生成](docs/tutorials/first-generation.md)

### ハウツー

- [インストール方法](docs/how-to/installation.md)
- [設定の使い方](docs/how-to/configuration.md)
- [予測機能の使い方](docs/how-to/prediction.md)
- [問題生成の使い方](docs/how-to/generation.md)
- [練習機能の使い方](docs/how-to/practice.md)

### リファレンス

- [CLI リファレンス](docs/reference/cli.md)
- [設定リファレンス](docs/reference/configuration.md)
- [ファイル形式](docs/reference/file-formats.md)
- [ファセット](docs/reference/facets.md)
- [重み](docs/reference/weights.md)
- [品質チェック](docs/reference/quality.md)
- [ログ](docs/reference/logging.md)
- [ストレージ/履歴](docs/reference/storage.md)

### 解説

- [アーキテクチャ概要](docs/explanation/architecture.md)
- [OpenAI API 連携の説明](docs/explanation/openai-integration.md)

## ライセンス

MIT License

## 名前の由来

「AuspiQ」の名前の由来は、ラテン語の「auspex」（卜占官）とQuizの「Q」を合成したものです。auspexは古代ローマにおいて鳥の飛び方などから未来を占う役職で、早押しクイズにおいて、問題文の途中までの情報から先の展開や答えを見通すようなイメージから名付けました。
