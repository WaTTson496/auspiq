"""ファイル入出力処理"""
import json
import csv
from pathlib import Path
from typing import List, Union, Optional, Dict, Any
from pydantic import ValidationError

from .models import QuizQuestion, AnalysisResult


class FileIOError(Exception):
    """ファイルI/Oエラー"""
    pass


class QuestionLoader:
    """問題文ファイルの読み込み機能"""

    @staticmethod
    def load_from_json(file_path: Union[str, Path]) -> List[QuizQuestion]:
        """JSON形式のファイルから問題文を読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            questions = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, str):
                        # 文字列のリストの場合
                        questions.append(QuizQuestion(original_text=item))
                    elif isinstance(item, dict):
                        # 辞書のリストの場合
                        text = item.get('question', item.get('text', ''))
                        answer = item.get('answer', item.get('correct_answer'))
                        if text:
                            questions.append(QuizQuestion(
                                original_text=text,
                                correct_answer=answer
                            ))
            else:
                raise FileIOError("JSONファイルは文字列または辞書のリストである必要があります")

            return questions

        except FileNotFoundError:
            raise FileIOError(f"ファイルが見つかりません: {file_path}")
        except json.JSONDecodeError as e:
            raise FileIOError(f"無効なJSON形式です: {e}")
        except ValidationError as e:
            raise FileIOError(f"データ形式が無効です: {e}")

    @staticmethod
    def load_from_csv(file_path: Union[str, Path], question_column: str = 'question',
                     answer_column: Optional[str] = 'answer') -> List[QuizQuestion]:
        """CSV形式のファイルから問題文を読み込み"""
        try:
            questions = []
            with open(file_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)

                if question_column not in reader.fieldnames:
                    raise FileIOError(f"指定された問題文カラム '{question_column}' が見つかりません")

                for row in reader:
                    text = row.get(question_column, '').strip()
                    if text:
                        answer = None
                        if answer_column and answer_column in row:
                            answer = row[answer_column].strip() or None

                        questions.append(QuizQuestion(
                            original_text=text,
                            correct_answer=answer
                        ))

            return questions

        except FileNotFoundError:
            raise FileIOError(f"ファイルが見つかりません: {file_path}")
        except Exception as e:
            raise FileIOError(f"CSVファイルの読み込みエラー: {e}")

    @classmethod
    def load_questions(cls, file_path: Union[str, Path],
                      question_column: str = 'question',
                      answer_column: Optional[str] = 'answer') -> List[QuizQuestion]:
        """ファイル拡張子に基づいて自動的に適切な読み込み方法を選択"""
        path = Path(file_path)

        if not path.exists():
            raise FileIOError(f"ファイルが存在しません: {file_path}")

        suffix = path.suffix.lower()

        if suffix == '.json':
            return cls.load_from_json(path)
        elif suffix == '.csv':
            return cls.load_from_csv(path, question_column, answer_column)
        else:
            raise FileIOError(f"サポートされていないファイル形式です: {suffix}。JSON形式またはCSV形式を使用してください。")


class ResultWriter:
    """解析結果ファイルの書き込み機能"""

    @staticmethod
    def write_to_json(results: List[AnalysisResult], file_path: Union[str, Path]) -> None:
        """解析結果をJSON形式で書き込み"""
        try:
            # Pydanticモデルを辞書に変換
            output_data = {
                "questions": [result.model_dump() for result in results]
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            raise FileIOError(f"JSONファイルの書き込みエラー: {e}")

    @staticmethod
    def write_statistics(results: List[AnalysisResult], file_path: Union[str, Path]) -> None:
        """統計情報をテキスト形式で書き込み"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("=== 解析結果統計 ===\n\n")
                f.write(f"処理問題数: {len(results)}\n\n")

                for i, result in enumerate(results, 1):
                    f.write(f"問題 {i}:\n")
                    f.write(f"  問題文: {result.question.original_text}\n")
                    f.write(f"  解析ポイント数: {len(result.analysis_points)}\n")

                    if result.analysis_points:
                        avg_prob = sum(point.total_probability for point in result.analysis_points) / len(result.analysis_points)
                        f.write(f"  平均蓋然性: {avg_prob:.1f}%\n")

                    f.write("\n")

        except Exception as e:
            raise FileIOError(f"統計ファイルの書き込みエラー: {e}")

    @classmethod
    def write_results(cls, results: List[AnalysisResult], file_path: Union[str, Path],
                     include_statistics: bool = False) -> None:
        """ファイル拡張子に基づいて適切な書き込み方法を選択"""
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == '.json':
            cls.write_to_json(results, path)
        elif suffix in ['.txt', '.text']:
            cls.write_statistics(results, path)
        else:
            # デフォルトはJSON形式
            json_path = path.with_suffix('.json')
            cls.write_to_json(results, json_path)
            if include_statistics:
                stats_path = path.with_suffix('.txt')
                cls.write_statistics(results, stats_path)