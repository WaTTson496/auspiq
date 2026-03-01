# 生成プロンプトテンプレートを差し替える

このページは、生成用プロンプトのテンプレートを差し替えるときの作業手順です。

## 触る場所

- `src/auspiq/prompts/system_prompt.md`
- `src/auspiq/prompts/generation/question_template.md`
- `src/auspiq/question_prompt.py`
- `src/auspiq/question_generator.py`

## 手順

1. 変更対象が system prompt か generation user prompt かを切り分けます。
2. JSON 出力契約 `question` / `answer` / `question_type` を壊さないようにテンプレートを更新します。
3. facet context の埋め込み項目を減らすなら downstream の品質や一貫性への影響を確認します。
4. 実際に `generate --format json` を回して JSON がパースできるか確認します。

## 注意

- prediction 系 prompt と generation 系 prompt は実装が分かれています
- `PromptTemplate` の legacy user template は生成本体では使っていません
- テンプレート差し替えは自由度が高い一方、JSON 契約を壊すと `QuestionGenerator` が失敗します

さらに、prompt の変更は見た目の文面だけでなく、quality report の傾向や生成の再現性にも影響します。テンプレート差し替え後は、単発と複数生成の両方を実行し、失敗形も確認する必要があります。
