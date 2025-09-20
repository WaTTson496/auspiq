"""練習コマンドの実装"""
import json
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

import click
from rich.console import Console

from ..config import ConfigManager
from ..file_io import QuestionLoader, ResultWriter
from ..models import PracticeQuestion, AnalysisResult, AnalysisPoint
from ..practice import PracticeEngine
from ..logging_config import get_logger

logger = get_logger(__name__)


@click.command()
@click.option(
    '--file', '-f',
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help='解析済み問題ファイルのパス'
)
@click.option(
    '--threshold', '-t',
    type=int,
    default=80,
    help='自動一時停止の蓋然性閾値 (0-100)'
)
@click.option(
    '--speed', '-s',
    type=float,
    default=0.1,
    help='文字表示速度（秒）'
)
@click.option(
    '--start-from', '-n',
    type=int,
    default=0,
    help='開始する問題番号（0から開始）'
)
@click.option(
    '--limit', '-l',
    type=int,
    help='練習する問題数の制限'
)
@click.help_option('-h', '--help')
@click.pass_context
def practice(
    ctx: click.Context,
    file: Path,
    threshold: int,
    speed: float,
    start_from: int,
    limit: Optional[int]
) -> None:
    """解析済み問題ファイルを使って早押し練習を行う"""

    # 設定の初期化
    config_manager = ConfigManager()
    config = config_manager.get_config()
    console = Console()

    try:
        # ファイル読み込み
        console.print(f"[blue]問題ファイルを読み込み中: {file}[/blue]")
        questions = _load_questions_from_file(file, start_from, limit)

        if not questions:
            console.print("[red]読み込める問題が見つかりませんでした[/red]")
            sys.exit(1)

        console.print(f"[green]{len(questions)}問を読み込みました[/green]")

        # 練習エンジンの初期化と設定
        engine = PracticeEngine(console)
        engine.set_auto_pause_threshold(threshold)
        engine.set_display_speed(speed)

        console.print(f"設定:")
        console.print(f"  自動停止閾値: {threshold}%")
        console.print(f"  表示速度: {speed}秒/文字")

        # 練習セッション開始
        engine.start_session(questions)

    except FileNotFoundError:
        console.print(f"[red]ファイルが見つかりません: {file}[/red]")
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]JSONファイルの読み込みエラー: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        logger.error(f"練習実行中にエラーが発生しました: {e}")
        console.print(f"[red]エラーが発生しました: {e}[/red]")
        sys.exit(1)


def _load_questions_from_file(
    file_path: Path,
    start_from: int = 0,
    limit: Optional[int] = None
) -> List[PracticeQuestion]:
    """ファイルから練習用問題を読み込む"""

    if file_path.suffix.lower() == '.json':
        return _load_from_json(file_path, start_from, limit)
    else:
        raise ValueError(f"サポートされていないファイル形式: {file_path.suffix}")


def _load_from_json(
    file_path: Path,
    start_from: int = 0,
    limit: Optional[int] = None
) -> List[PracticeQuestion]:
    """JSONファイルから練習用問題を読み込む"""

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    practice_questions: List[PracticeQuestion] = []

    # 解析結果形式の場合
    if isinstance(data, dict) and 'questions' in data:
        results = [AnalysisResult.model_validate(q) for q in data['questions']]
        for result in results:
            if not result.question.correct_answer:
                raise ValueError("解答が必須です。すべての問題に解答を設定してください。")
            practice_question = PracticeQuestion(
                original_text=result.question.original_text,
                correct_answer=result.question.correct_answer,
                analysis_points=result.analysis_points
            )
            practice_questions.append(practice_question)

    # 解析結果以外の形式はサポートしない
    elif isinstance(data, list):
        raise ValueError("練習機能では解析結果ファイルのみサポートされています。予測機能で生成された解析結果ファイルを使用してください。")

    else:
        raise ValueError("サポートされていないJSON形式です")

    # スライス処理
    end_index = None
    if limit is not None:
        end_index = start_from + limit

    return practice_questions[start_from:end_index]


def _create_sample_questions() -> List[PracticeQuestion]:
    """サンプル問題を作成（テスト用）"""
    return [
        PracticeQuestion(
            original_text="静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？",
            correct_answer="富士山",
            analysis_points=[
                AnalysisPoint(
                    position=20,
                    text_so_far="静岡県と山梨県の県境に位置する、標高",
                    candidates=[],
                    total_probability=85
                )
            ]
        ),
        PracticeQuestion(
            original_text="電気回路に流れる電流の大きさは、電圧に比例し、電気抵抗に反比例するという物理学の法則を、提唱したドイツの物理学者の名から何というでしょう？",
            correct_answer="オームの法則",
            analysis_points=[
                AnalysisPoint(
                    position=45,
                    text_so_far="電気回路に流れる電流の大きさは、電圧に比例し、電気抵抗に反比例する",
                    candidates=[],
                    total_probability=90
                )
            ]
        )
    ]


# CLI用のヘルプドキュメント
PRACTICE_HELP = """
練習コマンドは解析済み問題ファイルを使用して早押しクイズの練習を行います。

対応ファイル形式:
- JSON形式の解析結果ファイルのみ

注意事項:
- 解析結果ファイル以外の形式はサポートされません
- 予測機能で生成された解析結果ファイルを使用してください

練習中の操作:
- Enter: 一時停止/再開
- 'a': 解答表示
- 'q': 練習終了
- 'n': 次の問題

例:
auspiq practice -f results.json
auspiq practice -f results.json --threshold 85 --speed 0.05
auspiq practice -f results.json --start-from 10 --limit 5
"""