# 使い始める

このガイドは、AuspiQ を使い始めるための最短手順です。インストール、API キー設定、動作確認までを一通り終えることを目的にします。

## 前提

- Python 3.13 以上
- OpenAI API キーを持っている

## 手順

1. 仮想環境を作成し、パッケージをインストールします。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

2. API キーを設定ファイルへ保存します。

```bash
auspiq config set api-key sk-...
```

3. 現在の設定を確認します。

```bash
auspiq config show
auspiq config check
```

4. 最小の実行確認を行います。

```bash
auspiq predict single "静岡県と山梨県の県境に位置する、標高/"
```

ここで `predict single` を使うのは、準備が正しく済んだかを最小コストで確認できるからです。`generate` や `practice` でもよいのですが、最初の検証としては、入力が単純で保存物も分かりやすい `predict single` が適しています。

## 成功した状態

- `config show` で `API Key` が未設定になっていない
- `config check` が通る
- `predict single` が候補を返し、`results/auspiq_single_YYYYMMDD_HHMMSS.json` を作る

## よくある分岐

- API キーを環境変数だけで済ませたい場合:
  現状の実装では、`config show` は `OPENAI_API_KEY` を認識しますが、実行系コマンドは設定ファイル上の `api_key` を前提に動きます。まず `config set api-key ...` を使ってください。

- 設定ファイルの場所を変えたい場合:
  グローバルオプション `--config-file` で切り替えられます。

- 先に `generate` を試したい場合:
  可能ですが、まず `predict single` で設定と API 接続を確認しておく方が、失敗時の切り分けが簡単です。

## 関連

- 設定と保存物の詳細は [configuration-and-artifacts.md](./configuration-and-artifacts.md)
- 設定キー一覧は [../reference/shared.md](../reference/shared.md)
