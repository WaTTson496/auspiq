"""推測機能コマンド群"""
import json
import click
from datetime import datetime
from pathlib import Path
from typing import Union, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..config import ConfigManager
from ..models import PredictionRequest, QuizQuestion, AnalysisPoint, AnalysisResult
from ..api_client import OpenAIClient, APIError, BatchAPIError
from ..batch_manager import BatchJobManager, BatchJobInfo
from ..file_io import QuestionLoader, ResultWriter, FileIOError
from ..logging_config import get_logger


logger = get_logger(__name__)
console = Console()

# コマンド実行時刻を保持するグローバル変数
_execution_timestamp: str = None

def _set_execution_timestamp(timestamp: str) -> None:
    """コマンド実行時の統一タイムスタンプを設定する"""
    global _execution_timestamp
    _execution_timestamp = timestamp

def _get_execution_timestamp() -> str:
    """コマンド実行時の統一タイムスタンプを取得する"""
    global _execution_timestamp
    if _execution_timestamp is None:
        _execution_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _execution_timestamp

def _get_default_output_path(command_type: str, extension: str = "json") -> Path:
    """デフォルトの出力ファイルパスを生成する"""
    timestamp = _get_execution_timestamp()
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    filename = f"auspiq_{command_type}_{timestamp}.{extension}"
    return results_dir / filename


def _load_questions_for_predict(file_path: Union[str, Path]) -> List[QuizQuestion]:
    """推測機能専用の問題読み込み（解答必須、対応ファイル形式限定）"""
    path = Path(file_path)

    if not path.exists():
        raise FileIOError(f"ファイルが存在しません: {file_path}")

    suffix = path.suffix.lower()

    # JSON/CSV のみサポート
    if suffix == '.json':
        questions = QuestionLoader.load_from_json(path)
    elif suffix == '.csv':
        questions = QuestionLoader.load_from_csv(path)
    else:
        raise FileIOError(f"サポートされていないファイル形式です: {suffix}。JSON形式またはCSV形式を使用してください。")

    # すべての問題に解答があることを確認
    for i, question in enumerate(questions, 1):
        if not question.correct_answer:
            raise FileIOError(f"解答が必須です。問題 {i} 「{question.original_text[:50]}...」に解答を設定してください。")

    return questions


@click.group()
@click.help_option('-h', '--help')
def predict():
    """問題文推測機能"""
    pass


@predict.command()
@click.argument('text', type=str)
@click.option('--max-candidates', '-m', default=5, type=click.IntRange(1, 10),
              help='推測候補の最大数 (1-10)')
@click.option('--output', '-o', type=click.Path(),
              help='結果をファイルに出力')
@click.option('--format', 'output_format',
              type=click.Choice(['table', 'json'], case_sensitive=False),
              default='table', help='出力形式')
@click.help_option('-h', '--help')
@click.pass_context
def single(ctx, text, max_candidates, output, output_format):
    """単発推測 - 問題文の途中から続きを推測

    TEXTには問題文の途中まで（押しポイントまで）を入力してください。
    例: "静岡県と山梨県の県境に位置する、標高/"
    """
    logger.info("=== Starting single prediction command ===")
    logger.debug(f"Input parameters: text='{text}', max_candidates={max_candidates}, output={output}, format={output_format}")

    try:
        logger.info("Loading configuration...")
        config_path = ctx.obj.get('config_file')
        logger.debug(f"Config file path: {config_path}")

        config_manager = ConfigManager(config_path=config_path)
        config = config_manager.get_config()
        logger.debug(f"Loaded config: api_key={'***' if config.api_key else 'None'}, model={config.model}, max_tokens={config.max_tokens}")

        logger.info("Initializing OpenAI client...")
        client = OpenAIClient(config)

        # リクエストを作成
        logger.info("Creating prediction request...")
        request = PredictionRequest(
            text_so_far=text,
            max_candidates=max_candidates
        )
        logger.debug(f"Request object created: {request.model_dump()}")

        console.print(f"[blue]推測実行中...[/blue]")
        console.print(f"入力: {text}")

        # ログに記録
        logger.info(f"Starting API call for prediction: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        logger.debug(f"Full input text: '{text}'")

        # 推測実行
        result = client.predict_quiz_continuation(request)

        logger.info(f"API call completed successfully")
        logger.debug(f"Response details: {len(result.candidates)} candidates, total_probability={result.total_probability}%")

        for i, candidate in enumerate(result.candidates):
            logger.debug(f"Candidate {i+1}: '{candidate.full_text}' -> {candidate.answer} ({candidate.probability}%)")

        # 結果表示
        logger.info(f"Displaying results in {output_format} format...")
        if output_format == 'table':
            _display_prediction_table(result)
        else:
            _display_prediction_json(result)

        # ファイル出力
        logger.info("Saving results to file...")
        if not output:
            output = _get_default_output_path("single", "json")
            logger.debug(f"Generated automatic output path: {output}")
        else:
            logger.debug(f"Using specified output path: {output}")

        _save_prediction_result(result, output, output_format)
        logger.info(f"Results saved successfully to: {output}")
        console.print(f"[green]結果を {output} に保存しました。[/green]")

        logger.info("=== Single prediction command completed successfully ===")

    except APIError as e:
        logger.error(f"API error occurred: {e}")
        console.print(f"[red]API エラー: {e}[/red]")
        raise click.ClickException(str(e))
    except Exception as e:
        logger.error(f"Unexpected error in single prediction: {e}")
        logger.exception("Full exception details:")
        console.print(f"[red]推測に失敗しました: {e}[/red]")
        raise click.ClickException(str(e))


@predict.command()
@click.argument('text', type=str)
@click.argument('answer', type=str, default='')
@click.option('--step', '-s', default=1, type=click.IntRange(1, 20),
              help='解析ステップ間隔（文字数）')
@click.option('--min-length', default=1, type=click.IntRange(1, 50),
              help='解析開始最小文字数')
@click.option('--output', '-o', type=click.Path(),
              help='結果をファイルに出力')
@click.option('--format', 'output_format',
              type=click.Choice(['table', 'json'], case_sensitive=False),
              default='table', help='出力形式')
@click.help_option('-h', '--help')
@click.pass_context
def full(ctx, text, answer, step, min_length, output, output_format):
    """全文解析 - 問題文全体を解析して各押しポイントでの推測精度を分析

    TEXTには完全な問題文を入力してください。ANSWERは任意で、正解を入力できます。
    例:
    TEXT: "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？"
    ANSWER: "富士山" (任意)
    """
    logger.info("=== Starting full text analysis command ===")
    logger.debug(f"Input parameters: text='{text}', answer='{answer}', step={step}, min_length={min_length}, output={output}, format={output_format}")

    try:
        logger.info("Loading configuration...")
        config_manager = ConfigManager(config_path=ctx.obj.get('config_file'))
        config = config_manager.get_config()
        logger.debug(f"Loaded config: model={config.model}")

        logger.info("Initializing OpenAI client...")
        client = OpenAIClient(config)

        console.print(f"[blue]全文解析実行中...[/blue]")
        console.print(f"問題文: {text}")
        if answer:
            console.print(f"正解: {answer}")
        console.print(f"解析間隔: {step}文字ごと, 開始位置: {min_length}文字目以降")

        # 解析ポイントを計算
        analysis_points = []
        text_length = len(text)

        logger.info(f"Starting analysis: text_length={text_length}, positions={min_length} to {text_length-5} (step={step})")
        total_positions = len(range(min_length, text_length - 5, step))
        logger.debug(f"Will analyze {total_positions} positions")

        console.print()  # 空行を追加

        for i, pos in enumerate(range(min_length, text_length - 5, step), 1):
            text_so_far = text[:pos] + "/"

            logger.info(f"Analyzing position {i}/{total_positions}: pos={pos}, text='{text_so_far}'")

            # 進行状況とポイント情報を表示
            console.print(f"[bold blue]位置 {pos} ({i}/{total_positions})[/bold blue]")
            console.print(f"[dim]入力:[/dim] {text_so_far.replace('/', '[red]/[/red]')}")

            logger.debug(f"Creating prediction request for position {pos}")
            request = PredictionRequest(
                text_so_far=text_so_far,
                max_candidates=5
            )
            logger.debug(f"Request details: text_so_far='{text_so_far}', max_candidates=5")

            try:
                logger.info(f"Making API call for position {pos}...")
                prediction_result = client.predict_quiz_continuation(request)

                logger.info(f"Position {pos}: API call successful")
                logger.debug(f"Position {pos}: received {len(prediction_result.candidates)} candidates, total_probability={prediction_result.total_probability}%")

                # 各候補の詳細ログ
                for j, candidate in enumerate(prediction_result.candidates, 1):
                    logger.debug(f"  Position {pos} - Candidate {j}: '{candidate.full_text}' -> {candidate.answer} ({candidate.probability}%)")

                # リアルタイムで結果を表示
                _display_realtime_result(prediction_result, pos)

                logger.debug(f"Creating analysis point for position {pos}")
                analysis_point = AnalysisPoint(
                    position=pos,
                    text_so_far=text_so_far,
                    candidates=prediction_result.candidates,
                    total_probability=prediction_result.total_probability
                )
                analysis_points.append(analysis_point)
                logger.info(f"Successfully processed position {pos} ({i}/{total_positions})")

            except APIError as e:
                logger.error(f"API error at position {pos}: {e}")
                logger.warning(f"Failed to analyze position {pos}: {e}")
                logger.debug(f"Continuing with next position after error at {pos}")
                console.print(f"[red]エラー: {e}[/red]")
                continue

            console.print()  # 各ポイント間に空行

        # 解析結果を作成
        logger.info(f"Creating analysis result with {len(analysis_points)} successful analysis points")
        question = QuizQuestion(original_text=text, correct_answer=answer)
        result = AnalysisResult(
            question=question,
            analysis_points=analysis_points
        )
        logger.debug(f"Analysis result created successfully")

        # 解析完了の概要表示
        console.print(f"[bold green]解析完了![/bold green]")
        console.print(f"[dim]解析ポイント数: {len(analysis_points)}, 対象文字数: {text_length}[/dim]")

        # 概要テーブル表示
        logger.info(f"Displaying summary in {output_format} format...")
        if output_format == 'table':
            _display_analysis_summary(result)
        else:
            _display_analysis_json(result)

        # ファイル出力
        logger.info("Saving analysis results to file...")
        if not output:
            output = _get_default_output_path("full", "json")
            logger.debug(f"Generated automatic output path: {output}")
        else:
            logger.debug(f"Using specified output path: {output}")

        _save_analysis_result(result, output, output_format)
        logger.info(f"Analysis results saved successfully to: {output}")
        console.print(f"[green]結果を {output} に保存しました。[/green]")

        logger.info("=== Full text analysis command completed successfully ===")

    except APIError as e:
        logger.error(f"API error during analysis: {e}")
        console.print(f"[red]API エラー: {e}[/red]")
        raise click.ClickException(str(e))
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        logger.exception("Full exception details:")
        console.print(f"[red]解析に失敗しました: {e}[/red]")
        raise click.ClickException(str(e))


@predict.command()
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
@click.option('--save-raw-results', is_flag=True,
              help='デバッグ用にraw結果をファイルに保存（--retrieveと組み合わせ）')
@click.option('--list-jobs', is_flag=True,
              help='バッチジョブ一覧を表示')
@click.help_option('-h', '--help')
@click.pass_context
def batch(ctx, input_file, output, mode, step, min_length, use_batch_api, completion_window,
          submit, check_status, retrieve_job, save_raw_results, list_jobs):
    """一括処理 - ファイルから問題文を読み込んで一括で推測・解析

    ## 使用方法:

    ### 1. リアルタイム処理（従来）
    auspiq batch --input questions.txt

    ### 2. バッチAPI ジョブ投入（推奨）
    auspiq batch --input questions.txt --use-batch-api --submit

    ### 3. ジョブ一覧表示
    auspiq batch --list-jobs

    ### 4. ジョブステータス確認
    auspiq batch --status [JOB_ID]

    ### 5. 結果取得
    auspiq batch --retrieve [JOB_ID] --output results.json

    ### 6. 結果取得（デバッグ用raw結果も保存）
    auspiq batch --retrieve [JOB_ID] --output results.json --save-raw-results

    入力ファイル形式（解答必須）:
    - JSON: [{"question": "問題文1", "answer": "解答1"}, ...]
    - CSV: question,answer カラム（answer は必須）
    """
    logger.info("=== Starting batch processing command ===")
    logger.debug(f"Input parameters: input_file={input_file}, output={output}, mode={mode}, "
                 f"step={step}, min_length={min_length}, use_batch_api={use_batch_api}, "
                 f"submit={submit}, check_status={check_status}, retrieve_job={retrieve_job}, "
                 f"save_raw_results={save_raw_results}, list_jobs={list_jobs}")

    try:
        # 引数の検証
        action_count = sum([
            bool(input_file),  # 通常処理またはジョブ投入
            bool(check_status),  # ステータス確認
            bool(retrieve_job),  # 結果取得
            bool(list_jobs)  # ジョブ一覧
        ])

        if action_count != 1:
            console.print("[red]以下から1つのアクションを選択してください:[/red]")
            console.print("  --input: 新しい処理を開始")
            console.print("  --status [JOB_ID]: ジョブステータス確認")
            console.print("  --retrieve [JOB_ID]: 結果取得")
            console.print("  --list-jobs: ジョブ一覧表示")
            raise click.ClickException("複数のアクションが指定されました")

        # 設定読み込み
        logger.info("Loading configuration...")
        config_manager = ConfigManager(config_path=ctx.obj.get('config_file'))
        config = config_manager.get_config()

        # バッチジョブ管理機能
        job_manager = BatchJobManager()

        # === ジョブ一覧表示 ===
        if list_jobs:
            _display_job_list(job_manager)
            return

        # === ジョブステータス確認 ===
        if check_status:
            _check_job_status(check_status, config, job_manager)
            return

        # === 結果取得 ===
        if retrieve_job:
            _retrieve_job_results(retrieve_job, config, job_manager, output, save_raw_results)
            return

        # === 新規処理開始 ===
        if input_file:
            if use_batch_api and submit:
                # バッチAPIジョブ投入
                _submit_batch_job(input_file, mode, step, min_length, completion_window, config, job_manager)
            elif use_batch_api and not submit:
                console.print("[yellow]バッチAPIを使用する場合は --submit フラグが必要です[/yellow]")
                console.print("例: auspiq batch --input questions.txt --use-batch-api --submit")
                raise click.ClickException("--submit フラグが必要です")
            else:
                # 従来のリアルタイム処理
                _process_realtime_batch(input_file, output, mode, step, min_length, config)

    except BatchAPIError as e:
        logger.error(f"Batch API processing failed: {e}")
        console.print(f"[red]バッチAPI処理に失敗しました: {e}[/red]")
        raise click.ClickException(str(e))
    except APIError as e:
        logger.error(f"API error during batch processing: {e}")
        console.print(f"[red]API エラー: {e}[/red]")
        raise click.ClickException(str(e))
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        logger.exception("Full exception details:")
        console.print(f"[red]処理に失敗しました: {e}[/red]")
        raise click.ClickException(str(e))


def _display_job_list(job_manager: BatchJobManager) -> None:
    """ジョブ一覧を表示"""
    jobs = job_manager.list_jobs(limit=20)

    if not jobs:
        console.print("[yellow]バッチジョブが見つかりませんでした[/yellow]")
        return

    table = Table(title="バッチジョブ一覧", show_header=True, header_style="bold magenta")
    table.add_column("ジョブID", style="cyan", width=20, overflow="ellipsis")
    table.add_column("ステータス", style="green", width=12)
    table.add_column("作成日時", style="blue", width=16)
    table.add_column("問題数", style="yellow", width=8, justify="right")
    table.add_column("モード", style="white", width=8)
    table.add_column("入力ファイル", style="dim", width=30, overflow="ellipsis")

    for job in jobs:
        # 日時フォーマット
        try:
            from datetime import datetime
            created_at = datetime.fromisoformat(job.created_at)
            created_str = created_at.strftime("%m-%d %H:%M")
        except:
            created_str = job.created_at[:16] if len(job.created_at) > 16 else job.created_at

        # ステータス色分け
        status_style = {
            "submitted": "[yellow]submitted[/yellow]",
            "validating": "[blue]validating[/blue]",
            "in_progress": "[blue]in_progress[/blue]",
            "finalizing": "[blue]finalizing[/blue]",
            "completed": "[green]completed[/green]",
            "failed": "[red]failed[/red]",
            "expired": "[red]expired[/red]",
            "cancelled": "[red]cancelled[/red]",
        }.get(job.status, job.status)

        table.add_row(
            job.job_id[-20:],  # 末尾20文字
            status_style,
            created_str,
            str(job.questions_count),
            job.mode,
            job.input_file.split('/')[-1] if '/' in job.input_file else job.input_file  # ファイル名のみ
        )

    console.print(table)


def _check_job_status(job_id: str, config, job_manager: BatchJobManager) -> None:
    """ジョブステータスを確認"""
    console.print(f"[blue]ジョブステータス確認中...[/blue] {job_id}")

    # ローカルジョブ情報を取得
    local_job = job_manager.get_job(job_id)
    if not local_job:
        console.print(f"[red]ジョブ {job_id} がローカル記録に見つかりません[/red]")
        return

    try:
        # OpenAIからステータス取得
        client = OpenAIClient(config)
        status_info = client.get_batch_job_status(job_id)

        # ローカル情報を更新
        if status_info['status'] != local_job.status:
            job_manager.update_job_status(job_id, status_info['status'])

        # 結果表示
        console.print(Panel(_format_job_status_info(status_info, local_job), title=f"ジョブ情報: {job_id[:12]}...", border_style="blue"))

    except Exception as e:
        console.print(f"[red]ステータス取得に失敗: {e}[/red]")


def _format_job_status_info(status_info: dict, local_job: BatchJobInfo) -> str:
    """ジョブステータス情報をフォーマット"""
    from datetime import datetime

    lines = []
    lines.append(f"[bold]ジョブID:[/bold] {status_info['id']}")
    lines.append(f"[bold]ステータス:[/bold] {status_info['status']}")
    lines.append(f"[bold]入力ファイル:[/bold] {local_job.input_file}")
    lines.append(f"[bold]処理モード:[/bold] {local_job.mode}")
    lines.append(f"[bold]問題数:[/bold] {local_job.questions_count}")

    # 作成日時
    try:
        created_at = datetime.fromtimestamp(status_info['created_at'])
        lines.append(f"[bold]作成日時:[/bold] {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    except:
        lines.append(f"[bold]作成日時:[/bold] {status_info.get('created_at', 'N/A')}")

    # 完了日時
    if status_info.get('completed_at'):
        try:
            completed_at = datetime.fromtimestamp(status_info['completed_at'])
            lines.append(f"[bold]完了日時:[/bold] {completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        except:
            lines.append(f"[bold]完了日時:[/bold] {status_info['completed_at']}")

    # リクエスト数統計
    if status_info.get('request_counts'):
        req_counts = status_info['request_counts']
        lines.append(f"[bold]リクエスト統計:[/bold]")
        if hasattr(req_counts, 'total'):
            lines.append(f"  総数: {req_counts.total}")
        if hasattr(req_counts, 'completed'):
            lines.append(f"  完了: {req_counts.completed}")
        if hasattr(req_counts, 'failed'):
            lines.append(f"  失敗: {req_counts.failed}")

    # エラー情報
    if status_info.get('errors'):
        lines.append(f"[bold red]エラー:[/bold red] {status_info['errors']}")

    return "\n".join(lines)


def _retrieve_job_results(job_id: str, config, job_manager: BatchJobManager, output: str, save_raw_results: bool = False) -> None:
    """ジョブ結果を取得"""
    console.print(f"[blue]結果取得中...[/blue] {job_id}")

    # ローカルジョブ情報を取得
    local_job = job_manager.get_job(job_id)
    if not local_job:
        console.print(f"[red]ジョブ {job_id} がローカル記録に見つかりません[/red]")
        return

    try:
        # 元の問題リストを読み込み
        questions = job_manager.get_job_input_questions(local_job)

        # 結果取得
        client = OpenAIClient(config)
        results = client.retrieve_batch_results(job_id, questions, local_job.mode, save_raw_results)

        # 出力ファイル決定
        if not output:
            output = _get_default_output_path(f"batch_{job_id[:8]}", "json")

        # 結果保存
        ResultWriter.write_results(results, output)

        # ローカル情報更新
        job_manager.update_job_status(job_id, "completed", output_file=str(output))

        console.print(f"[green]結果を取得し、{output} に保存しました[/green]")
        if save_raw_results:
            console.print(f"[dim]（デバッグ用のraw結果もlogsディレクトリに保存されました）[/dim]")
        console.print(f"処理成功: {len(results)}/{len(questions)} 問")

    except Exception as e:
        console.print(f"[red]結果取得に失敗: {e}[/red]")


def _submit_batch_job(input_file: str, mode: str, step: int, min_length: int,
                     completion_window: str, config, job_manager: BatchJobManager) -> None:
    """バッチAPIジョブを投入"""
    from datetime import datetime
    from pathlib import Path

    console.print(f"[blue]バッチAPIジョブ投入中...[/blue]")
    console.print(f"入力ファイル: {input_file}")

    # ファイル読み込み（解答必須チェック付き）
    questions = _load_questions_for_predict(input_file)
    console.print(f"読み込み問題数: {len(questions)}")
    console.print(f"処理モード: {mode}")
    console.print(f"完了期限: {completion_window}")

    # ジョブ投入
    client = OpenAIClient(config)
    job_id = client.submit_batch_job(
        questions=questions,
        mode=mode,
        step=step,
        min_length=min_length,
        completion_window=completion_window
    )

    # ローカル記録を保存
    job_info = BatchJobInfo(
        job_id=job_id,
        input_file=str(Path(input_file).absolute()),
        mode=mode,
        step=step,
        min_length=min_length,
        questions_count=len(questions),
        created_at=datetime.now().isoformat(),
        status="submitted"
    )
    job_manager.save_job(job_info)

    console.print(f"[green]バッチジョブを投入しました[/green]")
    console.print(f"[bold]ジョブID:[/bold] {job_id}")
    console.print()
    console.print("[dim]次のコマンドでステータス確認:[/dim]")
    console.print(f"  auspiq batch --status {job_id}")
    console.print()
    console.print("[dim]結果取得コマンド（完了後）:[/dim]")
    console.print(f"  auspiq batch --retrieve {job_id} --output results.json")
    console.print("[dim]（デバッグ用raw結果も保存したい場合: --save-raw-results を追加）[/dim]")


def _process_realtime_batch(input_file: str, output: str, mode: str, step: int, min_length: int, config) -> None:
    """従来のリアルタイム処理"""
    console.print(f"[blue]リアルタイム処理実行中...[/blue]")
    console.print(f"入力ファイル: {input_file}")

    # ファイル読み込み（解答必須チェック付き）
    questions = _load_questions_for_predict(input_file)
    console.print(f"読み込み問題数: {len(questions)}")

    # 出力ファイルを決定
    if not output:
        output = _get_default_output_path("batch", "json")

    console.print(f"出力ファイル: {output}")
    console.print(f"処理モード: {mode}")

    client = OpenAIClient(config)
    results = []

    for i, question in enumerate(questions, 1):
        logger.info(f"Processing question {i}/{len(questions)}: '{question.original_text[:50]}{'...' if len(question.original_text) > 50 else ''}'")
        console.print(f"[dim]処理中... {i}/{len(questions)}: {question.original_text[:50]}...[/dim]")

        try:
            if mode == 'single':
                # 単発推測モード（問題文の中間地点で推測）
                text_length = len(question.original_text)
                mid_point = max(min_length, text_length // 2)
                text_so_far = question.original_text[:mid_point] + "/"

                request = PredictionRequest(
                    text_so_far=text_so_far,
                    max_candidates=5
                )

                prediction_result = client.predict_quiz_continuation(request)

                # 単発推測結果をAnalysisResultに変換
                analysis_point = AnalysisPoint(
                    position=mid_point,
                    text_so_far=text_so_far,
                    candidates=prediction_result.candidates,
                    total_probability=prediction_result.total_probability
                )

                result = AnalysisResult(
                    question=question,
                    analysis_points=[analysis_point]
                )

            else:
                # 全文解析モード
                analysis_points = []
                text_length = len(question.original_text)

                for pos in range(min_length, text_length - 5, step):
                    text_so_far = question.original_text[:pos] + "/"

                    request = PredictionRequest(
                        text_so_far=text_so_far,
                        max_candidates=5
                    )

                    try:
                        prediction_result = client.predict_quiz_continuation(request)

                        analysis_point = AnalysisPoint(
                            position=pos,
                            text_so_far=text_so_far,
                            candidates=prediction_result.candidates,
                            total_probability=prediction_result.total_probability
                        )
                        analysis_points.append(analysis_point)

                    except APIError as e:
                        logger.warning(f"Failed to analyze position {pos} for question {i}: {e}")
                        continue

                result = AnalysisResult(
                    question=question,
                    analysis_points=analysis_points
                )

            results.append(result)

        except APIError as e:
            logger.error(f"Failed to process question {i}: {e}")
            console.print(f"[red]問題 {i} の処理に失敗: {e}[/red]")
            continue

    # 結果保存
    ResultWriter.write_results(results, output)

    console.print(f"[green]リアルタイム処理完了。結果を {output} に保存しました。[/green]")
    console.print(f"処理成功: {len(results)}/{len(questions)} 問")


def _display_prediction_table(result):
    """推測結果をテーブル形式で表示"""
    table = Table(title="推測結果", show_header=True, header_style="bold magenta")
    table.add_column("候補", style="cyan", width=70, overflow="fold")
    table.add_column("解答", style="green", width=20)
    table.add_column("蓋然性", justify="right", style="yellow", width=8)

    for i, candidate in enumerate(result.candidates, 1):
        table.add_row(
            f"{i}. {candidate.full_text}",
            candidate.answer,
            f"{candidate.probability}%"
        )

    console.print(table)
    console.print(f"[bold]合計蓋然性: {result.total_probability}% (残り{100-result.total_probability}%はその他の可能性)[/bold]")


def _display_prediction_json(result):
    """推測結果をJSON形式で表示"""
    json_data = result.model_dump()
    console.print(json.dumps(json_data, ensure_ascii=False, indent=2))


def _display_realtime_result(prediction_result, position):
    """リアルタイムで各ポイントの推測結果を表示"""
    console.print(f"[red]蓋然性:[/red] {prediction_result.total_probability}%")

    if prediction_result.candidates:
        # 最有力候補を強調表示
        top_candidate = prediction_result.candidates[0]
        console.print(f"[green]最有力:[/green] [cyan]{top_candidate.full_text}[/cyan]")
        console.print(f"[yellow]  → {top_candidate.answer}[/yellow] ([bright_yellow]{top_candidate.probability}%[/bright_yellow])")

        # その他の候補（上位3つまで）
        if len(prediction_result.candidates) > 1:
            other_candidates = prediction_result.candidates[1:4]  # 最大3つまで
            if other_candidates:
                candidate_texts = []
                for candidate in other_candidates:
                    candidate_texts.append(f"{candidate.answer} ({candidate.probability}%)")
                console.print(f"[dim]その他: {', '.join(candidate_texts)}[/dim]")
    else:
        console.print("[red]推測候補なし[/red]")


def _display_analysis_summary(result):
    """解析結果の概要をテーブル形式で表示"""
    console.print(f"\n[bold magenta]解析概要[/bold magenta]")

    # 概要テーブル
    summary_table = Table(title="解析結果概要")
    summary_table.add_column("位置", style="cyan", width=8)
    summary_table.add_column("蓋然性", style="red", width=10)
    summary_table.add_column("最有力候補", style="green", width=40, overflow="fold")
    summary_table.add_column("確信度", style="yellow", width=10)

    for point in result.analysis_points:
        if point.candidates:
            top_candidate = point.candidates[0]
            summary_table.add_row(
                str(point.position),
                f"{point.total_probability}%",
                f"{top_candidate.answer}",
                f"{top_candidate.probability}%"
            )

    console.print(summary_table)

    # 統計情報
    if result.analysis_points:
        total_probs = [p.total_probability for p in result.analysis_points]
        avg_prob = sum(total_probs) / len(total_probs)
        max_prob = max(total_probs)
        min_prob = min(total_probs)

        console.print(f"\n[bold blue]統計情報[/bold blue]")
        console.print(f"平均蓋然性: {avg_prob:.1f}%")
        console.print(f"最高蓋然性: {max_prob}% (位置: {[p.position for p in result.analysis_points if p.total_probability == max_prob][0]})")
        console.print(f"最低蓋然性: {min_prob}% (位置: {[p.position for p in result.analysis_points if p.total_probability == min_prob][0]})")


def _display_analysis_table(result):
    """解析結果をリスト形式で表示"""
    console.print(Panel(result.question.original_text, title="対象問題文", border_style="blue"))

    console.print("\n[bold magenta]解析ポイント別推測結果[/bold magenta]")
    console.print("=" * 120)

    for point in result.analysis_points:
        if point.candidates:
            console.print(f"\n[bold cyan]位置 {point.position}:[/bold cyan]")
            console.print(f"[dim]問題文（途中まで）:[/dim] {point.text_so_far.replace('/', '[red]/[/red]')}")
            console.print(f"[red]合計蓋然性:[/red] {point.total_probability}%")
            console.print(f"[green]推測候補:[/green]")

            for i, candidate in enumerate(point.candidates, 1):
                console.print(f"  {i}. [cyan]{candidate.full_text}[/cyan]")
                console.print(f"     [yellow]解答:[/yellow] {candidate.answer} [yellow]({candidate.probability}%)[/yellow]")
                if i < len(point.candidates):  # 最後の候補でなければ区切り線
                    console.print("     " + "-" * 60)

    console.print("=" * 120)


def _display_analysis_json(result):
    """解析結果をJSON形式で表示"""
    json_data = result.model_dump()
    console.print(json.dumps(json_data, ensure_ascii=False, indent=2))


def _save_prediction_result(result, output_path, format_type):
    """推測結果をファイルに保存"""
    if format_type == 'json':
        json_data = result.model_dump()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
    else:
        # テーブル形式での保存は制限的なのでJSONで保存
        json_data = result.model_dump()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)


def _save_analysis_result(result, output_path, format_type):
    """解析結果をファイルに保存（batch形式と統一）"""
    # 単一のAnalysisResultをbatch形式（リスト）にラップ
    results = [result]
    # ResultWriter.write_resultsを使用してbatch形式で保存
    ResultWriter.write_results(results, output_path)