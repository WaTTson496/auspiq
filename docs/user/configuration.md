# 設定システム

AuspiQの設定システムについて説明します。

## 設定ファイル

設定は JSON 形式で `~/.auspiq.json` に保存されます。設定ファイルが存在しない場合は、デフォルト値が使用されます。

### 設定項目

| 項目 | デフォルト値 | 説明 |
|------|-------------|------|
| `api_key` | `null` | OpenAI API キー |
| `model` | `"gpt-4"` | 使用する OpenAI モデル |
| `threshold` | `80` | 自動停止の蓋然性閾値 (%) |
| `max_tokens` | `2000` | API リクエストの最大トークン数 |
| `temperature` | `0.1` | API リクエストの temperature |

### 設定ファイルの例

```json
{
  "api_key": "sk-your-openai-api-key",
  "model": "gpt-4",
  "threshold": 85,
  "max_tokens": 2000,
  "temperature": 0.1
}
```

## CLI コマンド

### 設定の表示

```bash
auspiq config show
```

現在の設定を表形式で表示します。API キーは最初の8文字のみ表示されます。

### 設定値の変更

```bash
auspiq config set <項目> <値>
```

#### 例

```bash
# API キーを設定
auspiq config set api-key sk-your-openai-api-key

# モデルを変更
auspiq config set model gpt-3.5-turbo

# 閾値を変更
auspiq config set threshold 90

# 最大トークン数を変更
auspiq config set max-tokens 1500

# temperature を変更
auspiq config set temperature 0.2
```

#### 設定項目のバリデーション

- `threshold`: 0-100の範囲
- `max_tokens`: 正の整数
- `temperature`: 0.0-2.0の範囲
- `model`: 推奨モデル（gpt-4, gpt-4-turbo, gpt-3.5-turbo）

### 設定のリセット

```bash
auspiq config reset
```

設定をデフォルト値にリセットします。確認プロンプトが表示されます。

### 設定ファイルの削除

```bash
auspiq config delete
```

設定ファイルを完全に削除します。確認プロンプトが表示されます。

### 設定の妥当性チェック

```bash
auspiq config check
```

現在の設定に問題がないかチェックします。以下の項目が検証されます：

- API キーの存在と形式
- モデル名の妥当性
- 閾値の範囲

## API キーの設定方法

### 方法1: 設定コマンドを使用

```bash
auspiq config set api-key sk-your-openai-api-key
```

### 方法2: 環境変数を使用

```bash
export OPENAI_API_KEY=sk-your-openai-api-key
```

環境変数が設定されている場合、設定ファイルに API キーがなくても環境変数の値が使用されます。設定ファイルの API キーが環境変数より優先されます。

## セキュリティ上の注意

- API キーは機密情報です。設定ファイルのアクセス権限に注意してください
- API キーをコードやログに含めないようにしてください
- 環境変数を使用する場合も、シェルの履歴に API キーが残らないよう注意してください

## カスタム設定ファイルパス

デフォルトの設定ファイルパス以外を使用したい場合は、`--config-file` オプションを使用できます：

```bash
auspiq config show --config-file /path/to/custom/config.json
auspiq config set api-key sk-key --config-file /path/to/custom/config.json
```

## トラブルシューティング

### 設定ファイルが読み込めない

設定ファイルが破損している場合は、以下のコマンドで削除して再作成できます：

```bash
auspiq config delete
auspiq config set api-key sk-your-api-key
```

### API キーが認識されない

1. 設定を確認：

   ```bash
   auspiq config show
   ```

2. 設定をチェック：

   ```bash
   auspiq config check
   ```

3. API キーの形式を確認（`sk-` で始まる必要があります）

### 権限エラー

設定ファイルのディレクトリに書き込み権限がない場合は、以下を確認してください：

```bash
ls -la ~/.auspiq.json
```

必要に応じてファイルの権限を変更してください：

```bash
chmod 600 ~/.auspiq.json
```
