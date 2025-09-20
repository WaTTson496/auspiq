# 予測機能ガイド

auspiqの予測機能について説明します。

## 予測機能の種類

### 1. 単発推測（Single Prediction）

問題文の途中から続きと解答を予測します。

### 2. 全文解析（Full Analysis）

問題文全体を解析し、各位置での推測精度を詳細に分析します。

### 3. 一括処理（Batch Processing）

複数の問題を一度に処理します。リアルタイム処理とバッチAPI（50%割引）の2つのモードが利用できます。

## 基本的な使用方法

### 単発推測の実行

```bash
# 基本的な使用方法
auspiq predict single "静岡県と山梨県の県境に位置する、標高"

# 推測候補数を指定（1-10個）
auspiq predict single "静岡県と山梨県の県境に位置する、標高" --max-candidates 3

# 結果をファイルに保存
auspiq predict single "静岡県と山梨県の県境に位置する、標高" --output result.json

# 出力形式を指定（table/json）
auspiq predict single "静岡県と山梨県の県境に位置する、標高" --format json
```

**入力のポイント：**

- 問題文は押したいポイントまで入力
- 文末に "/" を付けると、そこで区切られて解析されます
- 短すぎる文章だと推測精度が落ちる場合があります

### 全文解析の実行

```bash
# 問題文のみで解析
auspiq predict full "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？"

# 問題文と解答を指定して解析
auspiq predict full "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？" "富士山"

# 解析間隔を指定（デフォルト：1文字ごと）
auspiq predict full "問題文..." --step 3

# 解析開始位置を指定（デフォルト：1文字目から）
auspiq predict full "問題文..." --min-length 10

# 結果をファイルに保存
auspiq predict full "問題文..." --output analysis.json
```

**解析パラメータ：**

- `--step`: 何文字ごとに解析するか（1-20文字）
- `--min-length`: 解析を開始する最小文字数（1-50文字）

### エイリアスコマンド

よく使用する機能には短縮コマンドが用意されています：

```bash
# analyze コマンド（predict full のエイリアス）
auspiq analyze "問題文..." --max-candidates 3

# batch コマンド（predict batch のエイリアス）
auspiq batch --input questions.json --output results.json
```

## 一括処理（Batch Processing）

### ファイルからの一括処理

```bash
# CSVファイルから問題を読み込み
auspiq predict batch --input questions.csv

# JSONファイルから問題を読み込み
auspiq predict batch --input questions.json

# 処理モードを指定
auspiq predict batch --input questions.json --mode full

# 出力ファイルを指定
auspiq predict batch --input questions.csv --output results.json
```

**対応ファイル形式:**
- JSON形式（推奨）
- CSV形式

### リアルタイム処理

通常のリアルタイム処理では、問題を順次処理します：

```bash
# 単発推測モード（デフォルト）
auspiq predict batch --input questions.json --mode single

# 全文解析モード
auspiq predict batch --input questions.json --mode full --step 2 --min-length 5
```

## バッチAPI

OpenAIのBatch APIを使用します。

### バッチジョブの投入

```bash
# バッチジョブを投入（24時間以内に完了）
auspiq predict batch --input questions.json --use-batch-api --submit

# 全文解析でバッチジョブを投入
auspiq predict batch --input questions.json --mode full --use-batch-api --submit --step 2
```

### バッチジョブの管理

```bash
# 投入済みジョブの一覧を表示
auspiq predict batch --list-jobs

# ジョブのステータスを確認
auspiq predict batch --status [ジョブID]

# 完了したジョブの結果を取得
auspiq predict batch --retrieve [ジョブID] --output results.json
```

**バッチ処理の流れ：**

1. `--use-batch-api --submit`でジョブを投入
2. `--list-jobs`で進行状況を確認
3. ステータスが`completed`になったら`--retrieve`で結果を取得

## 結果の見方

### 単発推測の結果

```
推測結果
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 候補                                                                         ┃ 解答    ┃ 蓋然性 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1. 静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？         │ 富士山  │   45%  │
│ 2. 静岡県と山梨県の県境に位置する、標高3776メートルの山は？                      │ 富士山  │   25%  │
│ 3. 静岡県と山梨県の県境に位置する、標高の高い活火山といえば？                     │ 富士山  │   15%  │
└──────────────────────────────────────────────────────────────────────────────┘
合計蓋然性: 85% (残り15%はその他の可能性)
```

### 全文解析の結果

解析概要テーブルで各位置での推測精度を確認できます：

```
解析結果概要
┏━━━━━━━━┓━━━━━━━━━━┓━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓━━━━━━━━━━┓
┃ 位置   ┃ 蓋然性   ┃ 最有力候補                                             ┃ 確信度   ┃
┡━━━━━━━━┩━━━━━━━━━━┩━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩━━━━━━━━━━┩
│ 15     │ 30%      │ 富士山                                                 │ 15%      │
│ 20     │ 55%      │ 富士山                                                 │ 35%      │
│ 25     │ 85%      │ 富士山                                                 │ 45%      │
└────────┴──────────┴────────────────────────────────────────────────────────┴──────────┘

統計情報
平均蓋然性: 56.7%
最高蓋然性: 85% (位置: 25)
最低蓋然性: 30% (位置: 15)
```

**重要な指標：**

- **蓋然性**: その位置でAIが答えを確信する度合い
- **確信度**: 最有力候補の個別確信度
- **位置**: 問題文の文字数位置

## 詳細設定

### 出力ファイルの形式

指定しない場合、結果は自動的に`results/`ディレクトリに保存されます：

```
results/
├── auspiq_single_20240913_143022.json    # 単発推測
├── auspiq_full_20240913_143055.json      # 全文解析
└── auspiq_batch_20240913_143124.json     # 一括処理
```

### ログレベルの設定

詳細な処理状況を確認したい場合：

```bash
# 詳細ログを有効化
auspiq --verbose predict single "問題文..."

# ログレベルを指定
auspiq --log-level DEBUG predict single "問題文..."
```

## 制限と注意点

### API制限

- OpenAI APIのレート制限に注意してください
- 大量の問題を処理する場合はバッチAPIの使用を推奨
- APIキーの使用量に応じて課金されます

### 推測精度

- 問題文が短すぎる場合、推測精度が低下する可能性があります
- 専門的な問題や最新の情報が必要な問題では精度が低い場合があります
- AIの知識は学習データの範囲内に限定されます

### ファイルサイズ

- 大きなファイルを処理する場合はメモリ使用量にご注意ください
- バッチ処理では問題数に応じて処理時間が増加します

## 関連ドキュメント

- [練習機能ガイド](practice.md) - 解析結果を使った練習方法
- [バッチAPI活用ガイド](batch-api.md) - バッチ処理の詳細
- [ファイル形式ガイド](file-formats.md) - サポートされているファイル形式
- [設定ガイド](configuration.md) - API設定とカスタマイズ
