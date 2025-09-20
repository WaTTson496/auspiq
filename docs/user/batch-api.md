# バッチAPI活用ガイド

OpenAI Batch APIを使用して大量の問題を処理する方法を説明します。

## バッチAPIの特徴

### コスト面

- 50%のコスト削減
- 大量処理に適しています

### 処理面

- 非同期処理
- リトライ機能内蔵
- 大量データの安定処理

### 制約

- 24時間以内に完了
- リアルタイム性なし

## 基本的な使用方法

### 1. バッチジョブの投入

```bash
# 基本的なバッチ処理
auspiq batch --input questions.json --use-batch-api --submit

# 全文解析モードでバッチ処理
auspiq batch --input questions.json --mode full --use-batch-api --submit

# パラメータを指定してバッチ処理
auspiq batch --input questions.csv --mode full --step 2 --min-length 5 --use-batch-api --submit
```

**対応ファイル形式:**
- JSON形式（推奨）
- CSV形式

**重要**: `--use-batch-api`と`--submit`の両方が必要です。

### 2. ジョブの監視

```bash
# 投入済みジョブの一覧表示
auspiq batch --list-jobs

# 特定ジョブのステータス確認
auspiq batch --status batch_abc123def456

# 定期的なステータス確認（推奨）
watch -n 300 "auspiq batch --list-jobs"  # 5分ごとに更新
```

### 3. 結果の取得

```bash
# 完了したジョブの結果取得
auspiq batch --retrieve batch_abc123def456 --output final_results.json

# デバッグ用raw結果も保存する場合
auspiq batch --retrieve batch_abc123def456 --output final_results.json --save-raw-results

# 出力先を指定しない場合（自動的にファイル名生成）
auspiq batch --retrieve batch_abc123def456
```

## バッチ処理のワークフロー

### ステップ1: 問題ファイルの準備

まず処理したい問題をファイルに準備します：

**questions.json** (JSON形式、推奨)

```json
[
  {
    "question": "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？",
    "answer": "富士山"
  },
  {
    "text": "電気回路に流れる電流の大きさは、電圧に比例し、電気抵抗に反比例するという物理学の法則を何というでしょう？",
    "correct_answer": "オームの法則"
  },
  {
    "question": "1859年にチャールズ・ダーウィンが発表した、生物の進化に関する著作のタイトルは何でしょう？",
    "answer": "種の起源"
  }
]
```

**questions.csv** (CSV形式)

```csv
question,answer
静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？,富士山
電気回路に流れる電流の大きさは、電圧に比例し、電気抵抗に反比例するという物理学の法則を何というでしょう？,オームの法則
1859年にチャールズ・ダーウィンが発表した、生物の進化に関する著作のタイトルは何でしょう？,種の起源
```

### ステップ2: ジョブ投入と設定

```bash
# 詳細設定でジョブ投入
auspiq batch --input questions.json \
                     --mode full \
                     --step 2 \
                     --min-length 10 \
                     --use-batch-api \
                     --submit
```

投入後の表示例：

```
バッチAPIジョブ投入中...
入力ファイル: questions.json
読み込み問題数: 3
処理モード: full
完了期限: 24h
✅ バッチジョブを投入しました
ジョブID: batch_abc123def456

次のコマンドでステータス確認:
  auspiq batch --status batch_abc123def456

結果取得コマンド（完了後）:
  auspiq batch --retrieve batch_abc123def456 --output results.json
（デバッグ用raw結果も保存したい場合: --save-raw-results を追加）
```

### ステップ3: 進行状況の監視

```bash
# ジョブ一覧で全体の状況確認
auspiq batch --list-jobs
```

表示例：

```
バッチジョブ一覧
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓━━━━━━━━━━━━━┓━━━━━━━━━━━━━━━━┓━━━━━━━━┓━━━━━━━━┓━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ジョブID                 ┃ ステータス  ┃ 作成日時       ┃ 問題数 ┃ モード ┃ 入力ファイル                 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━┩━━━━━━━━━━━━━┩━━━━━━━━━━━━━━━━┩━━━━━━━━┩━━━━━━━━┩━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ abc123def456             │ in_progress │ 09-13 14:30   │ 3      │ full   │ questions.json               │
└──────────────────────────┴─────────────┴────────────────┴────────┴────────┴──────────────────────────────┘
```

### ステップ4: 詳細ステータス確認

```bash
# 特定ジョブの詳細状況
auspiq batch --status batch_abc123def456
```

表示例：

```
ジョブ情報: batch_abc123...
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ジョブID: batch_abc123def456789                                                              ┃
┃ ステータス: in_progress                                                                      ┃
┃ 入力ファイル: /path/to/questions.json                                                       ┃
┃ 処理モード: full                                                                            ┃
┃ 問題数: 3                                                                                   ┃
┃ 作成日時: 2024-09-13 14:30:22                                                              ┃
┃ リクエスト統計:                                                                             ┃
┃   総数: 45                                                                                  ┃
┃   完了: 30                                                                                  ┃
┃   失敗: 0                                                                                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### ステップ5: 結果取得

ステータスが`completed`になったら結果を取得：

```bash
# 結果取得
auspiq batch --retrieve batch_abc123def456 --output analysis_results.json

# デバッグ用raw結果も保存する場合
auspiq batch --retrieve batch_abc123def456 --output analysis_results.json --save-raw-results
```

#### 通常の成功時の表示

```
結果取得中... batch_abc123def456
✅ 結果を取得し、analysis_results.json に保存しました
処理成功: 3/3 問
```

#### `--save-raw-results`使用時の表示

```
結果取得中... batch_abc123def456
✅ 結果を取得し、analysis_results.json に保存しました
（デバッグ用のraw結果もlogsディレクトリに保存されました）
処理成功: 3/3 問
```

## 詳細設定オプション

### 処理モードの選択

```bash
# 単発推測モード（デフォルト）
auspiq batch --input questions.json --mode single --use-batch-api --submit

# 全文解析モード（推奨）
auspiq batch --input questions.json --mode full --use-batch-api --submit
```

### 全文解析パラメータ

```bash
# 細かい解析（高精度、高コスト）
auspiq batch --input questions.json \
                     --mode full \
                     --step 1 \
                     --min-length 5 \
                     --use-batch-api \
                     --submit

# 荒い解析（低コスト、実用的）
auspiq batch --input questions.json \
                     --mode full \
                     --step 3 \
                     --min-length 15 \
                     --use-batch-api \
                     --submit
```

### 完了期限の指定

```bash
# 24時間以内に完了（現在唯一のオプション）
auspiq batch --input questions.json \
                     --completion-window 24h \
                     --use-batch-api \
                     --submit
```

## ジョブステータスの種類

| ステータス | 説明 | 推定残り時間 | 対応 |
|-----------|------|-------------|------|
| `submitted` | 投入完了、処理待ち | 数分～数時間 | 待機 |
| `validating` | 入力検証中 | 数分 | 待機 |
| `in_progress` | 処理実行中 | 1-12時間 | 定期確認 |
| `finalizing` | 結果整理中 | 数分 | もうすぐ完了 |
| `completed` | 処理完了 | - | 結果取得可能 |
| `failed` | 処理失敗 | - | エラー確認 |
| `expired` | 期限切れ | - | 再投入必要 |
| `cancelled` | キャンセル済み | - | 再投入必要 |

## 使用方法

### 1. 問題数に応じた戦略

```bash
# 小規模（～50問）: リアルタイム処理推奨
auspiq batch --input small_set.json

# 中規模（50～500問）: バッチAPI推奨
auspiq batch --input medium_set.json --use-batch-api --submit

# 大規模（500問～）: バッチAPI + 荒い解析
auspiq batch --input large_set.json --mode full --step 3 --use-batch-api --submit
```

### 2. コスト最適化

```bash
# 最安設定（実用性も保持）
auspiq batch --input questions.json \
                     --mode full \
                     --step 4 \
                     --min-length 20 \
                     --use-batch-api \
                     --submit

# 高精度設定（コスト高）
auspiq batch --input questions.json \
                     --mode full \
                     --step 1 \
                     --min-length 5 \
                     --use-batch-api \
                     --submit
```

### 3. 時間管理

```bash
# 夜間投入（翌朝には完了）
auspiq batch --input questions.json --use-batch-api --submit

# 監視スクリプトの例
while true; do
  auspiq batch --status batch_abc123def456
  sleep 1800  # 30分ごとにチェック
done
```

## デバッグ機能

### Raw結果の保存機能

問題が発生した際の詳細な調査のために、OpenAI Batch APIから返される生のレスポンスデータを保存できます。

#### 使用方法

```bash
# 結果取得時にraw結果も保存
auspiq batch --retrieve batch_abc123def456 --output results.json --save-raw-results
```

#### 保存される内容

- **保存場所**: `logs/raw_batch_results_{batch_id}_{timestamp}.json`
- **内容**: OpenAI Batch APIから返される未加工のJSON結果
- **用途**:
  - 予期しない結果が返された場合の原因調査
  - API仕様変更の検出
  - パフォーマンス問題の分析

#### ファイル例

```json
{
  "id": "batch_req_abc123",
  "custom_id": "request-1",
  "response": {
    "status_code": 200,
    "request_id": "req_456def",
    "body": {
      "id": "chatcmpl-789ghi",
      "object": "chat.completion",
      "choices": [
        {
          "index": 0,
          "message": {
            "role": "assistant",
            "content": "..."
          }
        }
      ]
    }
  }
}
```

## トラブルシューティング

### よくある問題と対処法

#### 1. ジョブが`failed`になった

```bash
# 詳細ステータス確認
auspiq batch --status [ジョブID]

# エラー内容を確認して再投入
auspiq batch --input questions_fixed.json --use-batch-api --submit
```

#### 2. 結果取得時にエラー

```bash
# ジョブが本当に完了しているか確認
auspiq batch --status [ジョブID]

# 出力ディレクトリの権限確認
ls -la results/

# 別の出力先を指定
auspiq batch --retrieve [ジョブID] --output /tmp/results.json
```

#### 3. 処理時間が異常に長い

- 24時間以上経過している場合は`expired`の可能性
- OpenAI APIの障害情報をチェック
- 必要に応じて再投入

#### 4. コストが予想以上に高い

```bash
# 解析パラメータを見直し
auspiq batch --input questions.json \
                     --mode single \  # full → single に変更
                     --use-batch-api \
                     --submit

# または step を大きくする
auspiq batch --input questions.json \
                     --mode full \
                     --step 5 \       # 1 → 5 に変更
                     --use-batch-api \
                     --submit
```

## ベストプラクティス

### 1. ジョブ管理

```bash
# 投入前にローカルで小さなサンプルをテスト
auspiq predict single "テスト問題"

# ジョブIDをメモ帳に保存
echo "Job ID: batch_abc123def456 - Started: $(date)" >> batch_jobs.log

# 定期チェックスクリプト
*/30 * * * * auspiq batch --list-jobs >> /var/log/batch_status.log
```

### 2. ファイル管理

```bash
# 入力ファイルのバックアップ
cp questions.json questions_backup_$(date +%Y%m%d).json

# 結果ファイルの整理
mkdir -p results/$(date +%Y%m)
auspiq batch --retrieve [ジョブID] --output results/$(date +%Y%m)/batch_results.json
```

### 3. コスト管理

```bash
# 予想コスト計算（概算）
問題数 × 解析ポイント数 × 0.0003円 ÷ 2（バッチ割引）

# 例：100問 × 30ポイント × 0.0003円 ÷ 2 = 約0.45円
```

## 関連ドキュメント

- [予測機能ガイド](prediction.md) - バッチ処理の元となる機能
- [ファイル形式ガイド](file-formats.md) - 入力ファイルの形式
- [設定ガイド](configuration.md) - APIキー設定
