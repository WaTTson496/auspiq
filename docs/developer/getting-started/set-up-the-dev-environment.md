# 開発環境をセットアップする

このページは、AuspiQ の開発環境を立ち上げるための最短手順をまとめたものです。

## 前提

- Python 3.13 以上
- OpenAI API キー

## 手順

1. 仮想環境を作成し、編集可能インストールを行います。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

2. API キーを設定します。

```bash
auspiq config set api-key sk-...
```

3. CLI が起動することを確認します。

```bash
auspiq --help
auspiq config show
```

4. テストと静的チェックの入口を確認します。

```bash
pytest
black --check src
flake8 src
mypy src
```

ここで重要なのは、開発環境構築を「インストールできた」で終わらせないことです。AuspiQ は CLI なので、依存関係が入っていても、設定読込、ログ作成、保存先作成、OpenAI 呼び出しのいずれかで初めて問題が表面化することがあります。

## 確認しておく保存物

- 設定ファイル: `~/.auspiq.json`
- ログ: `logs/auspiq_YYYYMMDD_HHMMSS.log`
- 解析結果: `results/`
- ジョブ台帳: `~/.auspiq-jobs.json`

これらの場所を最初に把握しておくと、後で「何が壊れたか」だけでなく、「どこまで進んだか」も追いやすくなります。

## 関連

- 実行フロー確認は [run-the-main-cli-flows-locally.md](./run-the-main-cli-flows-locally.md)
- コード配置は [understand-the-codebase-map.md](./understand-the-codebase-map.md)
