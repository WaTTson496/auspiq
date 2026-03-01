# 生成設定と重みを調整する

このページは、生成結果の傾向を `settings-file`、`facet-weight`、`code-weight`、`candidate_map`、`leaf_only` で調整するときの作業手順です。

## 触る場所

- `src/auspiq/commands/generate.py`
- `src/auspiq/generation_settings.py`
- `src/auspiq/facet_selector.py`
- `src/auspiq/weight_manager.py`
- `src/auspiq/data/facets/`
- `src/auspiq/data/weights/`

## 何がどこに効くか

- `question_type`、`quality.length_*`: 出力文と quality criteria
- `retry_count`、`retry_delay`: API retry
- `parallelism`: batch generation
- `candidate_map`、`leaf_only`: facet selection
- `facet-weight`、`code-weight`: selection 時の重み補正
- `stage`: 読み込む weight data の切り替え

## 基本手順

1. まず `generate --format json --output out.json` を基準結果として取る
2. `settings-file` で再利用したい条件を固定する
3. 一時的な比較は CLI オプションで上書きする
4. `selection.steps` と `weight_selection` を見て、想定通りの層に効いているか確認する
5. 必要なら facet data や weight data を編集する

## `settings-file` の典型例

```json
{
  "stage": 0,
  "question_type": "SC",
  "candidate_map": {
    "subject": ["004", "005"]
  },
  "leaf_only": true,
  "quality": {
    "length_target": 90,
    "length_tolerance": 20,
    "min_score": 70
  },
  "weight_adjuster": {
    "facet_multipliers": {
      "subject": 1.2
    },
    "code_multipliers": {
      "subject": {
        "004": 0.8
      }
    }
  }
}
```

## 新しい weight stage を追加するとき

1. `src/auspiq/data/weights/stage_<n>_single_weights.json`
2. `src/auspiq/data/weights/stage_<n>_double_weights.json`
3. `src/auspiq/data/weights/stage_<n>_triple_weights.json`

この 3 種を揃える前提で考える。single だけ追加しても fallback は動くが、意図した調整かどうかは別です。

## 確認ポイント

- `candidate_map` の code が実在するか
- `leaf_only` により候補が過度に減っていないか
- `weight_adjuster` が facet と code のどちらに効いているか
- stage 変更で `weight_type` がどう変わったか
