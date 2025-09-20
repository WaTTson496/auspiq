# API リファレンス

設定システムの API 仕様について説明します。

## auspiq.config

### Config クラス

設定データを管理する Pydantic モデル。

```python
from auspiq.config import Config

config = Config(
    api_key="sk-your-api-key",
    model="gpt-4",
    threshold=85
)
```

#### フィールド

| フィールド | 型 | デフォルト | 説明 |
|-----------|----|-----------|----- |
| `api_key` | `Optional[str]` | `None` | OpenAI API キー |
| `model` | `str` | `"gpt-4"` | OpenAI モデル名 |
| `threshold` | `int` | `80` | 蓋然性閾値 (0-100) |
| `max_tokens` | `int` | `2000` | 最大トークン数 |
| `temperature` | `float` | `0.1` | Temperature (0.0-2.0) |

#### メソッド

継承された Pydantic メソッド：

- `model_dump()`: 辞書形式で設定を取得
- `model_validate(data)`: 辞書から Config インスタンスを作成

### ConfigManager クラス

設定ファイルの読み書きと管理を行うクラス。

```python
from auspiq.config import ConfigManager
from pathlib import Path

# デフォルトパスを使用
manager = ConfigManager()

# カスタムパスを使用
manager = ConfigManager(Path("/custom/config.json"))
```

#### コンストラクタ

```python
def __init__(self, config_path: Optional[Path] = None)
```

- `config_path`: 設定ファイルのパス（省略時は `~/.auspiq.json`）

#### メソッド

##### load()

```python
def load(self) -> Config
```

設定ファイルから設定を読み込みます。ファイルが存在しない場合はデフォルト設定を返します。

**戻り値**: `Config` - 設定オブジェクト

**例外**:

- `ValueError`: 設定ファイルの形式が不正な場合

##### save()

```python
def save(self, config: Optional[Config] = None) -> None
```

設定をファイルに保存します。

**パラメータ**:

- `config`: 保存する設定（省略時は現在の設定を使用）

**例外**:

- `ValueError`: 保存する設定がない場合、または保存に失敗した場合

##### get_config()

```python
def get_config(self) -> Config
```

現在の設定を取得します。`load()` のエイリアス。

**戻り値**: `Config` - 設定オブジェクト

##### update_config()

```python
def update_config(self, **kwargs) -> Config
```

設定を更新して保存します。

**パラメータ**:

- `**kwargs`: 更新する設定項目

**戻り値**: `Config` - 更新後の設定オブジェクト

**例**:

```python
manager.update_config(
    api_key="sk-new-key",
    threshold=90
)
```

##### reset_to_default()

```python
def reset_to_default(self) -> Config
```

設定をデフォルト値にリセットして保存します。

**戻り値**: `Config` - リセット後の設定オブジェクト

##### delete_config_file()

```python
def delete_config_file(self) -> None
```

設定ファイルを削除します。ファイルが存在しない場合は何もしません。

##### validate_api_key()

```python
def validate_api_key(self) -> bool
```

API キーが設定されているかチェックします。

**戻り値**: `bool` - API キーが有効な場合 True

##### get_api_key_from_env()

```python
def get_api_key_from_env(self) -> Optional[str]
```

環境変数 `OPENAI_API_KEY` から API キーを取得します。

**戻り値**: `Optional[str]` - 環境変数の値、または None

##### get_effective_api_key()

```python
def get_effective_api_key(self) -> Optional[str]
```

有効な API キーを取得します。設定ファイル優先、次に環境変数。

**戻り値**: `Optional[str]` - 有効な API キー、または None

## auspiq.commands.config

### CLI コマンド関数

Click デコレータを使用した CLI コマンド群。

#### show コマンド

```python
@config.command()
@click.option('--config-file', type=click.Path(path_type=Path))
def show(config_file: Optional[Path])
```

現在の設定を表形式で表示します。

#### set コマンド

```python
@config.command()
@click.argument('key')
@click.argument('value')
@click.option('--config-file', type=click.Path(path_type=Path))
def set(key: str, value: str, config_file: Optional[Path])
```

設定値を変更します。

**有効なキー**:

- `api-key` / `api_key`
- `model`
- `threshold`
- `max-tokens` / `max_tokens`
- `temperature`

#### reset コマンド

```python
@config.command()
@click.option('--config-file', type=click.Path(path_type=Path))
@click.confirmation_option(prompt='設定をデフォルトに戻しますか？')
def reset(config_file: Optional[Path])
```

設定をデフォルト値にリセットします。

#### delete コマンド

```python
@config.command()
@click.option('--config-file', type=click.Path(path_type=Path))
@click.confirmation_option(prompt='設定ファイルを削除しますか？')
def delete(config_file: Optional[Path])
```

設定ファイルを削除します。

#### check コマンド

```python
@config.command()
@click.option('--config-file', type=click.Path(path_type=Path))
def check(config_file: Optional[Path])
```

設定の妥当性をチェックし、問題があれば一覧表示します。

## 使用例

### 基本的な使用方法

```python
from auspiq.config import ConfigManager

# 設定マネージャーを作成
manager = ConfigManager()

# 設定を読み込み
config = manager.get_config()
print(f"現在のモデル: {config.model}")

# 設定を更新
manager.update_config(
    api_key="sk-your-api-key",
    model="gpt-3.5-turbo",
    threshold=85
)

# API キーの確認
if manager.validate_api_key():
    print("API キーが設定されています")
else:
    print("API キーが設定されていません")
```

### エラーハンドリング

```python
from auspiq.config import ConfigManager

manager = ConfigManager()

try:
    config = manager.load()
except ValueError as e:
    print(f"設定の読み込みに失敗: {e}")
    # デフォルト設定で続行
    config = manager.reset_to_default()

try:
    manager.update_config(threshold=150)  # 無効な値
except Exception as e:
    print(f"設定の更新に失敗: {e}")
```

### カスタム設定パス

```python
from pathlib import Path
from auspiq.config import ConfigManager

# プロジェクト固有の設定ファイルを使用
project_config = Path("./project-config.json")
manager = ConfigManager(project_config)

config = manager.get_config()
```
