"""predictコマンドのテスト"""
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.auspiq.commands.predict import _load_questions_for_predict
from src.auspiq.file_io import FileIOError
from src.auspiq.models import QuizQuestion


class TestPredictCommands:
    """predictコマンドのテストクラス"""

    def test_load_questions_for_predict_json_with_answers(self):
        """JSON形式で解答付き問題の読み込みテスト"""
        questions_data = [
            {
                "question": "テスト問題1",
                "answer": "テスト解答1"
            },
            {
                "text": "テスト問題2",
                "correct_answer": "テスト解答2"
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(questions_data, f, ensure_ascii=False)
            temp_path = f.name

        try:
            questions = _load_questions_for_predict(temp_path)
            assert len(questions) == 2
            assert questions[0].original_text == "テスト問題1"
            assert questions[0].correct_answer == "テスト解答1"
            assert questions[1].original_text == "テスト問題2"
            assert questions[1].correct_answer == "テスト解答2"
        finally:
            Path(temp_path).unlink()

    def test_load_questions_for_predict_json_missing_answer(self):
        """JSON形式で解答が欠けている場合のテスト"""
        questions_data = [
            {
                "question": "テスト問題1",
                "answer": "テスト解答1"
            },
            {
                "question": "テスト問題2"
                # answer が欠けている
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(questions_data, f, ensure_ascii=False)
            temp_path = f.name

        try:
            with pytest.raises(FileIOError, match="解答が必須です"):
                _load_questions_for_predict(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_questions_for_predict_txt_not_supported(self):
        """.txtファイルがサポートされていないことのテスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("テスト問題1\nテスト問題2\n")
            temp_path = f.name

        try:
            with pytest.raises(FileIOError, match="サポートされていないファイル形式"):
                _load_questions_for_predict(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_questions_for_predict_unsupported_format(self):
        """サポートされていないファイル形式のテスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as f:
            f.write("<questions></questions>")
            temp_path = f.name

        try:
            with pytest.raises(FileIOError, match="サポートされていないファイル形式です"):
                _load_questions_for_predict(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_questions_for_predict_csv_with_answers(self):
        """CSV形式で解答付き問題の読み込みテスト"""
        csv_content = """question,answer
テスト問題1,テスト解答1
テスト問題2,テスト解答2
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            questions = _load_questions_for_predict(temp_path)
            assert len(questions) == 2
            assert questions[0].original_text == "テスト問題1"
            assert questions[0].correct_answer == "テスト解答1"
            assert questions[1].original_text == "テスト問題2"
            assert questions[1].correct_answer == "テスト解答2"
        finally:
            Path(temp_path).unlink()

    def test_load_questions_for_predict_csv_missing_answer(self):
        """CSV形式で解答が欠けている場合のテスト"""
        csv_content = """question,answer
テスト問題1,テスト解答1
テスト問題2,
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            with pytest.raises(FileIOError, match="解答が必須です"):
                _load_questions_for_predict(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_questions_for_predict_file_not_found(self):
        """存在しないファイルのテスト"""
        with pytest.raises(FileIOError, match="ファイルが存在しません"):
            _load_questions_for_predict("nonexistent_file.json")