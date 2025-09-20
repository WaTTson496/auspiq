"""ファイル入出力処理のテスト"""
import json
import csv
import tempfile
from pathlib import Path
from typing import List

import pytest

from auspiq.file_io import QuestionLoader, ResultWriter, FileIOError
from auspiq.models import QuizQuestion, AnalysisResult, AnalysisPoint, PredictionCandidate


class TestQuestionLoader:
    """QuestionLoaderのテスト"""

    def test_load_from_json_string_list(self):
        """JSON形式（文字列リスト）からの読み込みテスト"""
        questions_data = [
            "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？",
            "電気回路に流れる電流の大きさは、電圧に比例し、電気抵抗に反比例するという物理学の法則を何というでしょう？"
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(questions_data, f, ensure_ascii=False)
            temp_path = f.name

        try:
            questions = QuestionLoader.load_from_json(temp_path)
            assert len(questions) == 2
            assert questions[0].original_text == questions_data[0]
            assert questions[1].original_text == questions_data[1]
            assert questions[0].correct_answer is None
            assert questions[1].correct_answer is None
        finally:
            Path(temp_path).unlink()

    def test_load_from_json_dict_list(self):
        """JSON形式（辞書リスト）からの読み込みテスト"""
        questions_data = [
            {
                "question": "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？",
                "answer": "富士山"
            },
            {
                "text": "電気回路に流れる電流の大きさは、電圧に比例し、電気抵抗に反比例するという物理学の法則を何というでしょう？",
                "correct_answer": "オームの法則"
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(questions_data, f, ensure_ascii=False)
            temp_path = f.name

        try:
            questions = QuestionLoader.load_from_json(temp_path)
            assert len(questions) == 2
            assert questions[0].correct_answer == "富士山"
            assert questions[1].correct_answer == "オームの法則"
        finally:
            Path(temp_path).unlink()

    def test_load_from_csv(self):
        """CSV形式からの読み込みテスト"""
        csv_data = [
            ['question', 'answer'],
            ['静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？', '富士山'],
            ['電気回路に流れる電流の大きさは、電圧に比例し、電気抵抗に反比例するという物理学の法則を何というでしょう？', 'オームの法則']
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
            temp_path = f.name

        try:
            questions = QuestionLoader.load_from_csv(temp_path)
            assert len(questions) == 2
            assert questions[0].original_text == csv_data[1][0]
            assert questions[0].correct_answer == csv_data[1][1]
            assert questions[1].correct_answer == csv_data[2][1]
        finally:
            Path(temp_path).unlink()

    def test_load_questions_auto_detect(self):
        """ファイル拡張子の自動検出テスト"""
        questions_data = ["テスト問題"]

        # JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(questions_data, f)
            json_path = f.name

        try:
            json_questions = QuestionLoader.load_questions(json_path)

            assert len(json_questions) == 1
            assert json_questions[0].original_text == "テスト問題"
        finally:
            Path(json_path).unlink()

    def test_file_not_found(self):
        """存在しないファイルのテスト"""
        with pytest.raises(FileIOError, match="ファイルが見つかりません"):
            QuestionLoader.load_from_json("nonexistent.json")

        with pytest.raises(FileIOError, match="ファイルが存在しません"):
            QuestionLoader.load_questions("nonexistent.json")

    def test_invalid_json(self):
        """無効なJSON形式のテスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            f.write("invalid json")
            temp_path = f.name

        try:
            with pytest.raises(FileIOError, match="無効なJSON形式"):
                QuestionLoader.load_from_json(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_unsupported_file_format(self):
        """サポートされていないファイル形式のテスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False, encoding='utf-8') as f:
            f.write("test")
            temp_path = f.name

        try:
            with pytest.raises(FileIOError, match="サポートされていないファイル形式"):
                QuestionLoader.load_questions(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_txt_file_not_supported(self):
        """テキストファイルがサポートされていないことのテスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("テスト問題1\nテスト問題2\n")
            temp_path = f.name

        try:
            with pytest.raises(FileIOError, match="サポートされていないファイル形式.*JSON形式またはCSV形式を使用してください"):
                QuestionLoader.load_questions(temp_path)
        finally:
            Path(temp_path).unlink()


class TestResultWriter:
    """ResultWriterのテスト"""

    def create_sample_results(self) -> List[AnalysisResult]:
        """テスト用のサンプル解析結果を作成"""
        candidate = PredictionCandidate(
            full_text="静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？",
            answer="富士山",
            probability=85
        )

        analysis_point = AnalysisPoint(
            position=20,
            text_so_far="静岡県と山梨県の県境に位置する、標高/",
            candidates=[candidate],
            total_probability=96
        )

        question = QuizQuestion(
            original_text="静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？",
            correct_answer="富士山"
        )

        return [AnalysisResult(
            question=question,
            analysis_points=[analysis_point]
        )]

    def test_write_to_json(self):
        """JSON形式での書き込みテスト"""
        results = self.create_sample_results()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            temp_path = f.name

        try:
            ResultWriter.write_to_json(results, temp_path)

            # 書き込まれた内容を確認
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert "questions" in data
            assert len(data["questions"]) == 1
            assert data["questions"][0]["question"]["original_text"] == results[0].question.original_text
        finally:
            Path(temp_path).unlink()

    def test_write_statistics(self):
        """統計情報の書き込みテスト"""
        results = self.create_sample_results()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            temp_path = f.name

        try:
            ResultWriter.write_statistics(results, temp_path)

            # 書き込まれた内容を確認
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "解析結果統計" in content
            assert "処理問題数: 1" in content
            assert "解析ポイント数: 1" in content
            assert "平均蓋然性: 96.0%" in content
        finally:
            Path(temp_path).unlink()

    def test_write_results_auto_detect(self):
        """ファイル拡張子の自動検出での書き込みテスト"""
        results = self.create_sample_results()

        # JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json_path = f.name

        # テキスト
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            txt_path = f.name

        try:
            ResultWriter.write_results(results, json_path)
            ResultWriter.write_results(results, txt_path)

            # JSON形式の確認
            assert Path(json_path).exists()
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            assert "questions" in json_data

            # テキスト形式の確認
            assert Path(txt_path).exists()
            with open(txt_path, 'r', encoding='utf-8') as f:
                txt_content = f.read()
            assert "解析結果統計" in txt_content
        finally:
            Path(json_path).unlink()
            Path(txt_path).unlink()