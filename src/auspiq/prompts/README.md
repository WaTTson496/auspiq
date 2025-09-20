# プロンプトファイル

このディレクトリには、OpenAI APIで使用するプロンプトテンプレートファイルが含まれています。

## ファイル構成

- **system_prompt.md**: システムプロンプト（競技クイズの説明）
- **user_prompt_template.md**: ユーザープロンプトテンプレート（予測リクエスト用）

## 編集時の注意事項

1. **エンコーディング**: UTF-8で保存してください
2. **改行コード**: LF（Unix形式）を使用してください
3. **テンプレート変数**: `user_prompt_template.md`では以下の変数が使用されます
   - `{max_candidates}`: 最大候補数
   - `{text_so_far}`: 問題文の途中まで

## テンプレート変数の例

```markdown
最大{max_candidates}つまで挙げてください。
問題文は以下の通りです：
{text_so_far}
```

## プロンプト更新後の確認

プロンプトファイルを更新した後は、以下で動作確認を行ってください：

```python
from auspiq.prompts import PromptTemplate

# プロンプトファイル検証
if PromptTemplate.validate_prompt_files():
    print("プロンプトファイルは正常です")
else:
    print("プロンプトファイルにエラーがあります")

# キャッシュクリア（開発時）
PromptTemplate.reload_prompts()
```
