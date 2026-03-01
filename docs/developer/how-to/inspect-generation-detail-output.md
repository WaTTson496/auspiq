# 生成詳細出力を確認する

このページは、`detail` 出力や batch failure を使って生成挙動を観察、診断するときの手順です。

## 見る対象

- `quality_report`
- `selection.steps`
- `weight_selection`
- `metadata`
- batch の `failures`
- `logs/auspiq_*.log`

## 基本手順

1. `generate --format json --output out.json` で detail JSON を保存する
2. `selection.steps` を見て、どの facet がどの候補数と確率で選ばれたか確認する
3. `weight_selection` を見て、`triple` / `double` / `single` / `base` のどれが使われたか確認する
4. `quality_report.issues` を見て、length、type、answer leak、facet 不整合のどれが効いているか確認する
5. batch では `failures[]` の `phase` と `exception_type` を見る

## 失敗の見方

- `facet_selection`: facet data、candidate_map、weight data を疑う
- `prompt_generation`: template path や facet context を疑う
- `api_call`: API 認証、rate limit、prompt / response を疑う
- `quality_validation`: quality criteria や生成結果の構文を疑う

## 保存物

- 画面の rich 表示だけでなく JSON を残す
- 必要なら batch の raw 結果や feedback も合わせて見る
