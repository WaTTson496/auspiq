"""practiceコマンドのテスト"""
import json
import pytest
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock

from src.auspiq.commands.practice import (
    practice,
    _load_questions_from_file,
    _load_from_json,
    _create_sample_questions
)
from src.auspiq.models import (
    PracticeQuestion,
    AnalysisResult,
    QuizQuestion,
    AnalysisPoint,
    PredictionCandidate
)
from src.auspiq.file_io import QuestionLoader, ResultWriter


class TestPracticeCommand:
    """practiceコマンドのテストクラス"""

    def test_create_sample_questions(self):
        """サンプル問題作成のテスト"""
        questions = _create_sample_questions()

        assert len(questions) == 2
        assert isinstance(questions[0], PracticeQuestion)
        assert questions[0].original_text.startswith("静岡県と山梨県")
        assert questions[0].correct_answer == "富士山"
        assert len(questions[0].analysis_points) == 1

    @pytest.fixture
    def sample_analysis_data(self):
        """サンプル解析データを作成"""
        return {
            "questions": [
                {
                    "question": {
                        "original_text": "テスト問題1",
                        "correct_answer": "テスト解答1"
                    },
                    "analysis_points": [
                        {
                            "position": 5,
                            "text_so_far": "テスト問",
                            "candidates": [
                                {
                                    "full_text": "テスト問題1",
                                    "answer": "テスト解答1",
                                    "probability": 85
                                }
                            ],
                            "total_probability": 85
                        }
                    ]
                }
            ]
        }


    def test_load_from_json_analysis_format(self, sample_analysis_data, tmp_path):
        """解析結果形式のJSON読み込みテスト"""
        # テスト用JSONファイルを作成
        json_file = tmp_path / "test_analysis.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sample_analysis_data, f, ensure_ascii=False)

        questions = _load_from_json(json_file)

        assert len(questions) == 1
        question = questions[0]
        assert question.original_text == "テスト問題1"
        assert question.correct_answer == "テスト解答1"
        assert len(question.analysis_points) == 1
        assert question.analysis_points[0].position == 5

    def test_load_from_json_question_list_format_not_supported(self, tmp_path):
        """問題リスト形式のJSON読み込みがサポートされないことのテスト"""
        # 問題リスト形式（サポート外）
        question_list = [
            {
                "original_text": "問題文1",
                "correct_answer": "解答1",
                "analysis_points": []
            }
        ]

        # テスト用JSONファイルを作成
        json_file = tmp_path / "test_questions.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(question_list, f, ensure_ascii=False)

        with pytest.raises(ValueError, match="練習機能では解析結果ファイルのみサポートされています"):
            _load_from_json(json_file)

    def test_load_from_json_with_slice(self, tmp_path):
        """スライス指定でのJSON読み込みテスト"""
        # 解析結果ファイル形式を作成
        analysis_results = {
            "questions": [
                {
                    "question": {
                        "original_text": "問題文1",
                        "correct_answer": "解答1"
                    },
                    "analysis_points": []
                },
                {
                    "question": {
                        "original_text": "問題文2",
                        "correct_answer": "解答2"
                    },
                    "analysis_points": []
                },
                {
                    "question": {
                        "original_text": "問題文3",
                        "correct_answer": "解答3"
                    },
                    "analysis_points": []
                }
            ]
        }

        json_file = tmp_path / "test_questions.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False)

        # start_from指定
        questions = _load_from_json(json_file, start_from=1)
        assert len(questions) == 2

        # start_fromとlimit指定
        questions = _load_from_json(json_file, start_from=0, limit=2)
        assert len(questions) == 2

        # start_fromとlimit指定（範囲外）
        questions = _load_from_json(json_file, start_from=1, limit=5)
        assert len(questions) == 2  # 利用可能な問題数まで

    def test_load_from_json_invalid_format(self, tmp_path):
        """無効な形式のJSON読み込みテスト"""
        invalid_data = {"invalid": "format"}
        json_file = tmp_path / "invalid.json"
        with open(json_file, 'w') as f:
            json.dump(invalid_data, f)

        with pytest.raises(ValueError, match="サポートされていないJSON形式"):
            _load_from_json(json_file)

    def test_load_from_json_string_format_not_supported(self, tmp_path):
        """文字列形式の問題は練習モードでサポートされないことのテスト"""
        string_questions = ["問題文1", "問題文2"]
        json_file = tmp_path / "string_questions.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(string_questions, f, ensure_ascii=False)

        with pytest.raises(ValueError, match="練習機能では解析結果ファイルのみサポートされています"):
            _load_from_json(json_file)

    def test_load_from_json_missing_answer_in_analysis_result(self, tmp_path):
        """解析結果形式で解答が欠けている場合のテスト"""
        analysis_data_no_answer = {
            "questions": [
                {
                    "question": {
                        "original_text": "テスト問題1",
                        "correct_answer": None
                    },
                    "analysis_points": []
                }
            ]
        }
        json_file = tmp_path / "no_answer_analysis.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data_no_answer, f, ensure_ascii=False)

        with pytest.raises(ValueError, match="解答が必須です"):
            _load_from_json(json_file)

    def test_load_from_json_practice_question_format_not_supported(self, tmp_path):
        """PracticeQuestion形式がサポートされないことのテスト"""
        practice_questions = [
            {
                "original_text": "問題文1",
                "correct_answer": "解答1",
                "analysis_points": []
            }
        ]
        json_file = tmp_path / "practice_questions.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(practice_questions, f, ensure_ascii=False)

        with pytest.raises(ValueError, match="練習機能では解析結果ファイルのみサポートされています"):
            _load_from_json(json_file)

    def test_load_questions_from_file_json(self, tmp_path):
        """JSON形式でのファイル読み込みテスト"""
        # 解析結果ファイル形式を作成
        analysis_results = {
            "questions": [
                {
                    "question": {
                        "original_text": "問題文1",
                        "correct_answer": "解答1"
                    },
                    "analysis_points": []
                },
                {
                    "question": {
                        "original_text": "問題文2",
                        "correct_answer": "解答2"
                    },
                    "analysis_points": []
                },
                {
                    "question": {
                        "original_text": "問題文3",
                        "correct_answer": "解答3"
                    },
                    "analysis_points": []
                }
            ]
        }

        json_file = tmp_path / "test.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False)

        questions = _load_questions_from_file(json_file)

        assert len(questions) == 3

    def test_load_questions_from_file_unsupported(self, tmp_path):
        """サポート外形式でのファイル読み込みテスト"""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("問題文")

        with pytest.raises(ValueError, match="サポートされていないファイル形式"):
            _load_questions_from_file(txt_file)

    @patch('src.auspiq.commands.practice.PracticeEngine')
    def test_practice_command_success(self, mock_engine_class, tmp_path):
        """practiceコマンド成功ケースのテスト"""
        # 解析結果ファイル形式を作成
        analysis_results = {
            "questions": [
                {
                    "question": {
                        "original_text": "問題文1",
                        "correct_answer": "解答1"
                    },
                    "analysis_points": []
                },
                {
                    "question": {
                        "original_text": "問題文2",
                        "correct_answer": "解答2"
                    },
                    "analysis_points": []
                }
            ]
        }

        # モック設定
        json_file = tmp_path / "test.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False)

        mock_engine_instance = Mock()
        mock_engine_class.return_value = mock_engine_instance

        runner = CliRunner()
        with patch('src.auspiq.commands.practice.ConfigManager'), \
             patch('src.auspiq.commands.practice.Console'):

            result = runner.invoke(practice, [
                '--file', str(json_file),
                '--threshold', '85',
                '--speed', '0.05'
            ])

            assert result.exit_code == 0
            mock_engine_instance.set_auto_pause_threshold.assert_called_once_with(85)
            mock_engine_instance.set_display_speed.assert_called_once_with(0.05)
            mock_engine_instance.start_session.assert_called_once()

    def test_practice_command_file_not_found(self):
        """practiceコマンド ファイル未存在のテスト"""
        runner = CliRunner()
        result = runner.invoke(practice, ['--file', 'nonexistent.json'])

        assert result.exit_code == 2  # clickのファイル存在チェックエラー

    def test_practice_command_json_error(self, tmp_path):
        """practiceコマンド JSON読み込みエラーのテスト"""
        # 無効なJSONファイルを作成
        json_file = tmp_path / "invalid.json"
        json_file.write_text("invalid json content")

        runner = CliRunner()
        with patch('src.auspiq.commands.practice.ConfigManager'), \
             patch('src.auspiq.commands.practice.Console'):

            result = runner.invoke(practice, ['--file', str(json_file)])
            assert result.exit_code == 1

    @patch('src.auspiq.commands.practice.PracticeEngine')
    def test_practice_command_empty_questions(self, mock_engine_class, tmp_path):
        """practiceコマンド 空問題リストのテスト"""
        json_file = tmp_path / "empty.json"
        with open(json_file, 'w') as f:
            json.dump([], f)

        runner = CliRunner()
        with patch('src.auspiq.commands.practice.ConfigManager'), \
             patch('src.auspiq.commands.practice.Console') as mock_console:

            result = runner.invoke(practice, ['--file', str(json_file)])

            assert result.exit_code == 1
            # エンジンは呼ばれない
            mock_engine_class.assert_not_called()

    @patch('src.auspiq.commands.practice.PracticeEngine')
    def test_practice_command_with_all_options(self, mock_engine_class, tmp_path):
        """practiceコマンド 全オプション指定のテスト"""
        # 解析結果ファイル形式を作成（30問）
        analysis_results = {
            "questions": [
                {
                    "question": {
                        "original_text": "テスト問題",
                        "correct_answer": "テスト解答"
                    },
                    "analysis_points": []
                } for _ in range(30)
            ]
        }

        json_file = tmp_path / "test.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False)

        mock_engine_instance = Mock()
        mock_engine_class.return_value = mock_engine_instance

        runner = CliRunner()
        with patch('src.auspiq.commands.practice.ConfigManager'), \
             patch('src.auspiq.commands.practice.Console'):

            result = runner.invoke(practice, [
                '--file', str(json_file),
                '--threshold', '75',
                '--speed', '0.2',
                '--start-from', '5',
                '--limit', '10'
            ])

            assert result.exit_code == 0
            mock_engine_instance.set_auto_pause_threshold.assert_called_once_with(75)
            mock_engine_instance.set_display_speed.assert_called_once_with(0.2)

            # start_sessionに渡された問題数をチェック
            call_args = mock_engine_instance.start_session.call_args[0]
            questions = call_args[0]
            assert len(questions) == 10  # limitで制限された数