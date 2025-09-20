"""メインCLIエントリーポイント"""
import click
from datetime import datetime

from .commands.config import config
from .commands.predict import predict
from .commands.practice import practice
from .config import ConfigManager
from .logging_config import setup_logging


@click.group()
@click.version_option(version="0.1.0")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config-file', '-c',
              type=click.Path(exists=False),
              help='Path to configuration file (default: ~/.auspiq.json)')
@click.option('--log-level', '-l',
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], case_sensitive=False),
              help='Set logging level (overrides LOG_LEVEL environment variable)')
@click.help_option('-h', '--help')
@click.pass_context
def main(ctx, verbose, config_file, log_level):
    """AuspiQ - OpenAI を使った競技クイズ練習ツール"""
    # コンテキストオブジェクトを初期化してグローバルオプションを保存
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config_file'] = config_file

    # 設定からログレベルを取得
    try:
        config_manager = ConfigManager(config_file)
        app_config = config_manager.get_config()
        console_log_level = app_config.console_log_level
        file_log_level = app_config.file_log_level
    except Exception:
        # 設定読み込みエラーの場合はデフォルト値を使用
        console_log_level = "INFO"
        file_log_level = "DEBUG"

    # コマンドライン引数でログレベルが指定された場合は優先
    if log_level:
        console_log_level = log_level
        file_log_level = log_level

    # 詳細モードが有効な場合はコンソールログレベルをDEBUGに設定
    if verbose:
        console_log_level = 'DEBUG'

    # 統一タイムスタンプを生成
    execution_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ログ設定を初期化
    log_file = setup_logging(
        console_level=console_log_level,
        file_level=file_log_level,
        timestamp=execution_timestamp
    )

    # predict モジュールでタイムスタンプを使用できるように設定
    from .commands.predict import _set_execution_timestamp
    _set_execution_timestamp(execution_timestamp)

    # 初回ログメッセージ（動作確認用）
    if verbose or console_log_level in ['DEBUG', 'INFO']:
        import click
        click.echo(f"ログファイル: {log_file}", err=True)


# コマンドを登録
main.add_command(config)
main.add_command(predict)
main.add_command(practice)

# 個別コマンドのエイリアス
@main.command()
@click.argument('text', type=str)
@click.option('--max-candidates', '-m', default=5, type=click.IntRange(1, 10),
              help='推測候補の最大数 (1-10)')
@click.option('--output', '-o', type=click.Path(),
              help='結果をファイルに出力')
@click.option('--format', 'output_format',
              type=click.Choice(['table', 'json'], case_sensitive=False),
              default='table', help='出力形式')
@click.pass_context
def analyze(ctx, text, max_candidates, output, output_format):
    """全文解析 - 問題文全体を解析して各押しポイントでの推測精度を分析

    predict full のエイリアス。
    """
    ctx.forward(predict.commands['full'])


@main.command()
@click.option('--input', '-i', 'input_file', type=click.Path(exists=True),
              help='入力ファイルパス (JSON, CSV, またはテキスト形式)')
@click.option('--output', '-o', type=click.Path(),
              help='出力ファイルパス（未指定時は results/auspiq_batch_YYYYMMDD_HHMMSS.json）')
@click.option('--mode', type=click.Choice(['single', 'full'], case_sensitive=False),
              default='single', help='処理モード: single=単発推測, full=全文解析')
@click.option('--step', '-s', default=1, type=click.IntRange(1, 20),
              help='全文解析時のステップ間隔（文字数）')
@click.option('--min-length', default=1, type=click.IntRange(1, 50),
              help='全文解析時の開始最小文字数')
@click.option('--use-batch-api', is_flag=True,
              help='OpenAI Batch APIを使用（50%割引、非同期処理）')
@click.option('--completion-window', default='24h',
              type=click.Choice(['24h'], case_sensitive=False),
              help='バッチAPI完了期限（現在は24hのみサポート）')
@click.option('--submit', is_flag=True,
              help='バッチAPIジョブを投入（--use-batch-apiと組み合わせ）')
@click.option('--status', 'check_status', type=str,
              help='バッチジョブのステータスを確認（ジョブID指定）')
@click.option('--retrieve', 'retrieve_job', type=str,
              help='完了したバッチジョブの結果を取得（ジョブID指定）')
@click.option('--list-jobs', is_flag=True,
              help='バッチジョブ一覧を表示')
@click.pass_context
def batch(ctx, input_file, output, mode, step, min_length, use_batch_api, completion_window,
          submit, check_status, retrieve_job, list_jobs):
    """一括処理 - ファイルから問題文を読み込んで一括で推測・解析

    predict batch のエイリアス。
    """
    ctx.forward(predict.commands['batch'])


if __name__ == "__main__":
    main()