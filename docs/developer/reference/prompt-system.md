# プロンプトシステム

このページは、prediction 系と generation 系を含む prompt 実装の境界をまとめたものです。

## 共通プロンプトローダ

- `src/auspiq/prompts.py`
- `PromptTemplate` が `system_prompt.md` と legacy `user_prompt_template.md` をキャッシュする

## 生成プロンプト

- system prompt: `src/auspiq/prompts/system_prompt.md`
- user template: `src/auspiq/prompts/generation/question_template.md`
- builder: `src/auspiq/question_prompt.py`

埋め込まれる情報:

- facet code
- label
- hierarchy
- including
- usage note
- scope note
- references
- question type hint
- relation hint
- difficulty hint
- output schema

## パーサ側の契約

- 生成応答は JSON object を前提にする
- 必須フィールドは `question`、`answer`、`question_type`
- ここを壊すと `QuestionGenerator` が失敗する

`question_type` は後段の quality validator や end-user 向けの表示にも流れるため、形式上存在するだけでなく、意味的にも破綻しにくい値である必要があります。

## 実装上の注意

- generation 本体は legacy `user_prompt_template.md` を使っていない
- prompt docs は prediction 系と generation 系を分けて書く必要がある

prompt の責務は、単に文体を指定することではありません。facet context をどう LLM に渡すか、どこまで JSON 契約を明示するか、難易度や関係性をどう誘導するかも含みます。
