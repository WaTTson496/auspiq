# ファイル形式ガイド

auspiqでサポートされている入力・出力ファイル形式の説明です。

## 入力ファイル形式

### 1. CSV形式 (.csv)

#### 特徴

- 表計算ソフトで編集可能
- 問題文と解答をセットで管理
- ヘッダー行必須

**必須カラム:**

- `question`: 問題文
- `answer`: 解答

**形式:**

```csv
question,answer
問題文1,解答1
問題文2,解答2
```

#### 例: quiz_data.csv

```csv
question,answer
静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？,富士山
電気回路に流れる電流の大きさは、電圧に比例し、電気抵抗に反比例するという物理学の法則を何というでしょう？,オームの法則
1859年にチャールズ・ダーウィンが発表した、生物の進化に関する著作のタイトルは何でしょう？,種の起源
```

#### 追加カラムの例

```csv
question,answer,category,difficulty
静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？,富士山,地理,easy
電気回路に流れる電流の大きさは、電圧に比例し、電気抵抗に反比例するという物理学の法則を何というでしょう？,オームの法則,物理,medium
```

#### 使用コマンド例

```bash
auspiq batch --input quiz_data.csv
```

### 2. JSON形式 - 問題リスト (.json)

#### 特徴

- 構造化されたデータ
- プログラムで処理しやすい
- 拡張可能

**基本形式:**

```json
[
  {
    "question": "問題文1",
    "answer": "解答1"
  },
  {
    "text": "問題文2",
    "correct_answer": "解答2"
  }
]
```

**フル形式 (メタデータ付き):**

```json
[
  {
    "question": "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？",
    "answer": "富士山",
    "category": "地理",
    "difficulty": "easy",
    "source": "地理検定2023"
  },
  {
    "text": "電気回路に流れる電流の大きさは、電圧に比例し、電気抵抗に反比例するという物理学の法則を何というでしょう？",
    "correct_answer": "オームの法則",
    "category": "物理",
    "difficulty": "medium"
  }
]
```

#### 使用コマンド例

```bash
auspiq batch --input questions.json
```

## 出力ファイル形式

### 1. 予測結果 (単発推測)

**ファイル名例:** `auspiq_single_20240913_143022.json`

**形式:**

```json
{
  "text_so_far": "静岡県と山梨県の県境に位置する、標高",
  "candidates": [
    {
      "full_text": "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？",
      "answer": "富士山",
      "probability": 45
    },
    {
      "full_text": "静岡県と山梨県の県境に位置する、標高3776メートルの山は？",
      "answer": "富士山",
      "probability": 25
    }
  ],
  "total_probability": 85
}
```

### 2. 全文解析結果

**ファイル名例:** `auspiq_full_20240913_143055.json`

**形式:**

```json
{
  "question": {
    "original_text": "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？",
    "correct_answer": "富士山"
  },
  "analysis_points": [
    {
      "position": 15,
      "text_so_far": "静岡県と山梨県の県境に位置する、標高/",
      "candidates": [
        {
          "full_text": "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？",
          "answer": "富士山",
          "probability": 30
        }
      ],
      "total_probability": 55
    },
    {
      "position": 20,
      "text_so_far": "静岡県と山梨県の県境に位置する、標高3776m/",
      "candidates": [
        {
          "full_text": "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？",
          "answer": "富士山",
          "probability": 45
        }
      ],
      "total_probability": 85
    }
  ]
}
```

### 3. 一括処理結果

**ファイル名例:** `auspiq_batch_20240913_143124.json`

**形式:**

```json
{
  "metadata": {
    "processed_at": "2024-09-13T14:31:24+09:00",
    "total_questions": 3,
    "successful_analyses": 3,
    "processing_mode": "full"
  },
  "questions": [
    {
      "question": {
        "original_text": "問題文1",
        "correct_answer": "解答1"
      },
      "analysis_points": [
        // 解析ポイントの配列
      ]
    },
    {
      "question": {
        "original_text": "問題文2",
        "correct_answer": "解答2"
      },
      "analysis_points": [
        // 解析ポイントの配列
      ]
    }
  ]
}
```

## 練習用ファイル形式

### 練習セッション対応形式

練習機能 (`practice` コマンド) では以下の形式を読み込めます：

**1. 解析結果形式 (推奨)**

```json
{
  "questions": [
    {
      "question": {
        "original_text": "問題文",
        "correct_answer": "解答"
      },
      "analysis_points": [
        {
          "position": 20,
          "text_so_far": "問題文の途中まで/",
          "candidates": [...],
          "total_probability": 85
        }
      ]
    }
  ]
}
```

**2. シンプル問題リスト形式**

```json
[
  {
    "original_text": "問題文1",
    "correct_answer": "解答1",
    "analysis_points": []
  },
  {
    "original_text": "問題文2",
    "correct_answer": "解答2",
    "analysis_points": []
  }
]
```

## 🛠️ ファイル変換ツール

### CSV → JSON 変換

```python
import csv
import json

def csv_to_json(csv_file, json_file):
    questions = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append({
                "original_text": row['question'],
                "correct_answer": row.get('answer', None)
            })

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

# 使用例
csv_to_json('quiz_data.csv', 'questions.json')
```


## 📋 ファイル形式の選択指針

### 用途別推奨形式

| 用途 | 推奨形式 | 理由 |
|------|----------|------|
| **Excel等で管理** | CSV (.csv) | 表計算ソフトで編集可能 |
| **プログラム連携** | JSON (.json) | 構造化データ、拡張可能 |
| **大量データ** | CSV (.csv) | ファイルサイズ効率 |
| **練習用** | 解析結果 (.json) | 自動停止機能対応 |

### データ量別推奨

| 問題数 | 推奨形式 | コメント |
|--------|----------|----------|
| ～10問 | JSON | 手軽な編集 |
| 10～100問 | CSV | 管理しやすさ |
| 100～1000問 | JSON | 処理効率 |
| 1000問～ | CSV + バッチAPI | 大量データ対応 |

## 🔧 ファイル形式トラブルシューティング

### よくあるエラーと対処法

#### 1. 文字エンコーディングエラー

```bash
# ファイルのエンコーディング確認
file -I questions.txt

# UTF-8に変換
iconv -f SHIFT_JIS -t UTF-8 questions_sjis.txt > questions.txt
```

#### 2. CSVの読み込みエラー

```bash
# CSV形式確認
head -5 questions.csv

# 必須カラム確認
csvcut -n questions.csv  # csvkit使用
```

#### 3. JSON形式エラー

```bash
# JSON形式確認
python -m json.tool questions.json

# バリデーション
jq '.' questions.json  # jq使用
```

#### 4. ファイルパスエラー

```bash
# 絶対パス使用
auspiq batch --input /full/path/to/questions.txt

# 現在ディレクトリからの相対パス確認
ls -la questions.txt
```

## 📁 ファイル管理のベストプラクティス

### ディレクトリ構造例

```
my_quiz_project/
├── input/
│   ├── questions_history.json
│   ├── questions_science.csv
│   └── contest_2024.json
├── output/
│   ├── results/
│   │   ├── history_analysis.json
│   │   └── science_batch_results.json
│   └── practice/
│       ├── history_practice.json
│       └── science_practice.json
└── scripts/
    ├── convert_csv_to_json.py
    └── prepare_practice_file.py
```

### ファイル命名規則

```bash
# 入力ファイル
questions_[カテゴリ]_[日付].json
quiz_[ソース]_[バージョン].csv

# 出力ファイル（自動生成）
auspiq_single_20240913_143022.json
auspiq_full_20240913_143055.json
auspiq_batch_20240913_143124.json

# 練習ファイル
practice_[カテゴリ]_[レベル].json
```

### バックアップ戦略

```bash
# 定期バックアップ
cp -r input/ backup/input_$(date +%Y%m%d)/
cp -r output/ backup/output_$(date +%Y%m%d)/

# 重要ファイルの世代管理
cp important_questions.json important_questions_v$(date +%Y%m%d).json
```

## 関連ドキュメント

- [予測機能ガイド](prediction.md) - 各機能での使用方法
- [バッチAPI活用ガイド](batch-api.md) - バッチ処理の詳細
- [練習機能ガイド](practice.md) - 練習用ファイルの活用
