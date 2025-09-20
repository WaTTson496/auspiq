# OpenAI API Integration

このドキュメントでは、AuspiQのOpenAI API連携機能について説明します。

## 概要

AuspiQは、OpenAI GPTモデルを使用して競技クイズの問題文の続きを予測する機能を提供します。これにより、早押しクイズの練習において、どのタイミングで答えが予測可能になるかを分析できます。

## アーキテクチャ

### 主要コンポーネント

1. **OpenAIClient** (`api_client.py`)
   - OpenAI APIとの通信を担当
   - エラーハンドリングとリトライ機能を含む

2. **データモデル** (`models.py`)
   - API リクエスト・レスポンスの構造定義
   - Pydantic による型安全性の確保

3. **プロンプトテンプレート** (`prompts.py`)
   - 競技クイズ専用のプロンプト管理
   - 一貫性のある推論を促すためのテンプレート

## 使用方法

### 基本的な使用例

```python
from auspiq.config import Config, ConfigManager
from auspiq.api_client import OpenAIClient
from auspiq.models import PredictionRequest

# 設定の読み込み
config_manager = ConfigManager()
config = config_manager.load()

# API クライアントの初期化
client = OpenAIClient(config)

# 予測リクエストの作成
request = PredictionRequest(
    text_so_far="静岡県と山梨県の県境に位置する、標高／",
    max_candidates=5
)

# 予測の実行
try:
    response = client.predict_quiz_continuation(request)
    
    print(f"候補数: {len(response.candidates)}")
    print(f"合計蓋然性: {response.total_probability}%")
    
    for i, candidate in enumerate(response.candidates, 1):
        print(f"{i}. {candidate.answer} ({candidate.probability}%)")
        print(f"   {candidate.full_text}")
        
except Exception as e:
    print(f"エラーが発生しました: {e}")
```

### 設定

API キーは以下の方法で設定できます：

1. **設定ファイル** (`~/.auspiq.json`)

```json
{
  "api_key": "your-openai-api-key",
  "model": "gpt-4",
  "max_tokens": 2000,
  "temperature": 0.1,
  "threshold": 80
}
```

2. **環境変数**

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

3. **プログラム内で直接指定**

```python
client = OpenAIClient(config, api_key="your-api-key")
```

## データモデル

### PredictionRequest

問題文の予測リクエストを表します。

```python
class PredictionRequest(BaseModel):
    text_so_far: str  # 問題文の途中まで（"／"で区切り）
    max_candidates: int = 5  # 最大候補数（1-10）
```

### PredictionResponse

予測結果のレスポンスを表します。

```python
class PredictionResponse(BaseModel):
    candidates: List[PredictionCandidate]  # 推測候補リスト
    total_probability: int  # 全候補の合計蓋然性（0-100%）
    text_so_far: str  # 入力された問題文
```

### PredictionCandidate

個々の推測候補を表します。

```python
class PredictionCandidate(BaseModel):
    full_text: str  # 完全な問題文
    answer: str  # 解答
    probability: int  # 蓋然性（0-100%）
```

## エラーハンドリング

### エラータイプ

1. **APIError** - 一般的なAPI エラー
2. **APIRateLimitError** - レート制限エラー
3. **APIValidationError** - レスポンス検証エラー

### リトライ機能

API呼び出しは自動的にリトライされます：

- デフォルトリトライ回数: 3回
- 指数バックオフによる待機時間調整
- レート制限エラーに対する特別な処理

```python
# リトライ設定のカスタマイズ
response = client.predict_quiz_continuation(
    request,
    retry_count=5,  # リトライ回数
    retry_delay=2.0  # 初期待機時間（秒）
)
```

## プロンプト設計

### プロンプト管理

プロンプトは外部ファイルとして管理され、保守性と柔軟性を向上させています：

- **システムプロンプト**: `src/auspiq/prompts/system_prompt.md`
- **ユーザープロンプトテンプレート**: `src/auspiq/prompts/user_prompt_template.md`

### プロンプトの特徴

**システムプロンプト**：

- SC型（コピュラ型）問題の説明
- OV型（呼称・命名型）問題の説明  
- 問題文の構造的特徴（文字数、情報配置など）
- 難易度設定の考え方

**ユーザープロンプト**：

- JSON形式でのレスポンスを要求
- 問題文候補（最大5つ）
- 各候補の解答と蓋然性
- 蓋然性の合計値

### プロンプトのカスタマイズ

プロンプトファイルを直接編集することで、カスタマイズが可能です：

```python
# プロンプト再読み込み（開発時）
from auspiq.prompts import PromptTemplate
PromptTemplate.reload_prompts()

# プロンプトファイル検証
if PromptTemplate.validate_prompt_files():
    print("プロンプトファイルは正常です")
```

## パフォーマンス考慮事項

### API使用量の最適化

1. **適切なmax_tokens設定**
   - デフォルト: 2000トークン
   - 長い問題文が予想される場合は調整

2. **temperature設定**
   - デフォルト: 0.1（一貫性重視）
   - より創造的な回答が必要な場合は調整

3. **バッチ処理**
   - 複数の問題を順次処理する際のレート制限対策
   - 適切な間隔での API呼び出し

### キャッシュ機能（将来実装予定）

同一の入力に対する重複したAPI呼び出しを防ぐため、結果のキャッシュ機能を検討中。

## セキュリティ

### API キー管理

- API キーは設定ファイルまたは環境変数で管理
- ソースコードに直接埋め込まない
- 適切なファイル権限設定（600推奨）

### レスポンス検証

- Pydantic による厳密な型チェック
- 不正なレスポンスの拒否
- セキュリティホールの防止

## トラブルシューティング

### よくある問題

1. **認証エラー**

   ```text
   APIError: OpenAI API authentication failed
   ```

   - API キーの確認
   - 有効期限の確認

2. **レート制限エラー**

   ```text
   APIRateLimitError: OpenAI API rate limit exceeded
   ```

   - 自動リトライが実行される
   - 必要に応じてリトライ間隔を調整

3. **モデルエラー**

   ```text
   APIError: OpenAI model 'gpt-4' not found
   ```

   - モデル名の確認
   - アカウントのモデルアクセス権限確認

### デバッグ方法

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# より詳細なエラー情報が出力される
```

### 接続テスト

```python
# API 接続のテスト
if client.test_connection():
    print("API connection is working")
else:
    print("API connection failed")
```

## 制限事項

1. **API 依存性**
   - インターネット接続が必要
   - OpenAI API の可用性に依存

2. **コスト**
   - API 使用料金が発生
   - 大量の問題処理時は注意

3. **レスポンス品質**
   - モデルの性能に依存
   - 100%の精度は保証されない

## 今後の改善予定

1. **非同期処理**
   - 複数の API 呼び出しの並列実行
   - パフォーマンス向上

2. **キャッシュ機能**
   - 結果のローカルキャッシュ
   - API 使用量の削減

3. **カスタムプロンプト**
   - ユーザー定義プロンプトのサポート
   - 分野特化の調整

4. **統計機能**
   - API 使用量の追跡
   - 精度指標の計算
