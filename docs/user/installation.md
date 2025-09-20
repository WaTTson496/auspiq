# インストールガイド

AuspiQのインストール方法について説明します。

## システム要件

- **Python**: 3.13 以上
- **オペレーティングシステム**: Windows, macOS, Linux
- **OpenAI API**: OpenAI のアカウントと API キー

## インストール

### 方法1: pipを使用（推奨）

```bash
pip install auspiq
```

### 方法2: 開発版をインストール

最新の開発版を使用したい場合：

```bash
git clone https://github.com/your-username/auspiq_quiz_trainer.git
cd auspiq_quiz_trainer
pip install -e .
```

## セットアップ

### 1. OpenAI API キーの取得

1. [OpenAI Platform](https://platform.openai.com/) にアクセス
2. アカウントを作成またはログイン
3. API Keys セクションで新しい API キーを作成
4. API キーをコピー（`sk-` で始まる文字列）

### 2. API キーの設定

#### 方法A: 設定コマンドを使用（推奨）

```bash
auspiq config set api-key sk-your-openai-api-key
```

#### 方法B: 環境変数を使用

**Linux/macOS:**

```bash
export OPENAI_API_KEY=sk-your-openai-api-key
```

**Windows (Command Prompt):**

```cmd
set OPENAI_API_KEY=sk-your-openai-api-key
```

**Windows (PowerShell):**

```powershell
$env:OPENAI_API_KEY="sk-your-openai-api-key"
```

### 3. インストールの確認

```bash
auspiq --version
auspiq config show
```

正常にインストールされていれば、バージョン情報と設定が表示されます。

## 初期設定

### 基本設定

```bash
# API キーの設定（まだの場合）
auspiq config set api-key sk-your-openai-api-key

# 使用するモデルの設定（オプション）
auspiq config set model gpt-4

# 蓋然性閾値の設定（オプション）
auspiq config set threshold 80
```

### 設定の確認

```bash
# 現在の設定を表示
auspiq config show

# 設定に問題がないかチェック
auspiq config check
```

## トラブルシューティング

### よくある問題

#### Python のバージョンが古い

```bash
python --version
```

Python 3.13 以上が必要です。バージョンが古い場合は Python をアップデートしてください。

#### pipのインストールに失敗する

```bash
# pipをアップデート
pip install --upgrade pip

# 仮想環境を使用
python -m venv venv
source venv/bin/activate  # Linux/macOS
# または
venv\Scripts\activate     # Windows

pip install auspiq
```

#### API キーが認識されない

1. API キーの形式を確認（`sk-` で始まっているか）
2. 設定を確認：

   ```bash
   auspiq config show
   ```

3. API キーの再設定：

   ```bash
   auspiq config set api-key sk-your-correct-api-key
   ```

#### 権限エラー

**Linux/macOS:**

```bash
# ユーザーレベルでインストール
pip install --user auspiq

# または sudo を使用（非推奨）
sudo pip install auspiq
```

**Windows:**

管理者としてコマンドプロンプトを実行してからインストールしてください。

## アンインストール

```bash
pip uninstall auspiq
```

設定ファイルも削除したい場合：

```bash
auspiq config delete  # アンインストール前に実行
```

または手動で削除：

**Linux/macOS:**

```bash
rm ~/.auspiq.json
```

**Windows:**

```cmd
del %USERPROFILE%\.auspiq.json
```

## 次のステップ

インストールが完了したら、[設定ガイド](configuration.md)を参照して詳細な設定方法を確認してください。
