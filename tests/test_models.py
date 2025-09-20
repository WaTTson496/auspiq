"""データモデルのテスト"""
import pytest
from pydantic import ValidationError

from auspiq.models import (
    PredictionCandidate,
    AnalysisPoint,
    QuizQuestion,
    AnalysisResult,
    PredictionRequest,
    PredictionResponse
)


class TestPredictionCandidate:
    """PredictionCandidate モデルのテスト"""
    
    def test_valid_candidate(self):
        """有効な候補データでモデルが作成されることを確認"""
        candidate = PredictionCandidate(
            full_text="静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？",
            answer="富士山",
            probability=85
        )
        
        assert candidate.full_text == "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？"
        assert candidate.answer == "富士山"
        assert candidate.probability == 85
    
    def test_probability_range_validation(self):
        """蓋然性の範囲検証が正常に動作することを確認"""
        # 有効な範囲
        candidate = PredictionCandidate(
            full_text="test",
            answer="test",
            probability=0
        )
        assert candidate.probability == 0
        
        candidate = PredictionCandidate(
            full_text="test", 
            answer="test",
            probability=100
        )
        assert candidate.probability == 100
        
        # 無効な範囲
        with pytest.raises(ValidationError):
            PredictionCandidate(
                full_text="test",
                answer="test", 
                probability=-1
            )
        
        with pytest.raises(ValidationError):
            PredictionCandidate(
                full_text="test",
                answer="test",
                probability=101
            )
    
    def test_required_fields(self):
        """必須フィールドが検証されることを確認"""
        with pytest.raises(ValidationError):
            PredictionCandidate(answer="test", probability=50)  # full_text missing
        
        with pytest.raises(ValidationError):
            PredictionCandidate(full_text="test", probability=50)  # answer missing
        
        with pytest.raises(ValidationError):
            PredictionCandidate(full_text="test", answer="test")  # probability missing


class TestAnalysisPoint:
    """AnalysisPoint モデルのテスト"""
    
    def test_valid_analysis_point(self):
        """有効な解析ポイントデータでモデルが作成されることを確認"""
        candidates = [
            PredictionCandidate(full_text="test1", answer="answer1", probability=60),
            PredictionCandidate(full_text="test2", answer="answer2", probability=30)
        ]
        
        point = AnalysisPoint(
            position=20,
            text_so_far="静岡県と山梨県の県境に位置する、標高／",
            candidates=candidates,
            total_probability=90
        )
        
        assert point.position == 20
        assert point.text_so_far == "静岡県と山梨県の県境に位置する、標高／"
        assert len(point.candidates) == 2
        assert point.total_probability == 90
    
    def test_position_validation(self):
        """位置の検証が正常に動作することを確認"""
        candidates = [PredictionCandidate(full_text="test", answer="test", probability=50)]
        
        # 有効な位置
        point = AnalysisPoint(
            position=0,
            text_so_far="test",
            candidates=candidates,
            total_probability=50
        )
        assert point.position == 0
        
        # 無効な位置
        with pytest.raises(ValidationError):
            AnalysisPoint(
                position=-1,
                text_so_far="test",
                candidates=candidates,
                total_probability=50
            )


class TestQuizQuestion:
    """QuizQuestion モデルのテスト"""
    
    def test_valid_question(self):
        """有効な問題データでモデルが作成されることを確認"""
        question = QuizQuestion(
            original_text="静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？",
            correct_answer="富士山"
        )
        
        assert question.original_text == "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？"
        assert question.correct_answer == "富士山"
    
    def test_optional_correct_answer(self):
        """正解が省略可能であることを確認"""
        question = QuizQuestion(
            original_text="test question"
        )
        
        assert question.original_text == "test question"
        assert question.correct_answer is None


class TestAnalysisResult:
    """AnalysisResult モデルのテスト"""
    
    def test_valid_analysis_result(self):
        """有効な解析結果データでモデルが作成されることを確認"""
        question = QuizQuestion(original_text="test question")
        candidates = [PredictionCandidate(full_text="test", answer="test", probability=50)]
        analysis_points = [
            AnalysisPoint(
                position=10,
                text_so_far="test／",
                candidates=candidates,
                total_probability=50
            )
        ]
        
        result = AnalysisResult(
            question=question,
            analysis_points=analysis_points
        )
        
        assert result.question == question
        assert len(result.analysis_points) == 1
        assert result.analysis_points[0].position == 10


class TestPredictionRequest:
    """PredictionRequest モデルのテスト"""
    
    def test_valid_request(self):
        """有効なリクエストデータでモデルが作成されることを確認"""
        request = PredictionRequest(
            text_so_far="静岡県と山梨県の県境に位置する、標高／",
            max_candidates=5
        )
        
        assert request.text_so_far == "静岡県と山梨県の県境に位置する、標高／"
        assert request.max_candidates == 5
    
    def test_default_max_candidates(self):
        """max_candidatesのデフォルト値が正しく設定されることを確認"""
        request = PredictionRequest(
            text_so_far="test／"
        )
        
        assert request.max_candidates == 5
    
    def test_max_candidates_range(self):
        """max_candidatesの範囲検証が正常に動作することを確認"""
        # 有効な範囲
        request = PredictionRequest(text_so_far="test／", max_candidates=1)
        assert request.max_candidates == 1
        
        request = PredictionRequest(text_so_far="test／", max_candidates=10)
        assert request.max_candidates == 10
        
        # 無効な範囲
        with pytest.raises(ValidationError):
            PredictionRequest(text_so_far="test／", max_candidates=0)
        
        with pytest.raises(ValidationError):
            PredictionRequest(text_so_far="test／", max_candidates=11)

    def test_empty_text_so_far(self):
        """空の問題文でバリデーションエラーが発生することを確認"""
        with pytest.raises(ValidationError) as exc_info:
            PredictionRequest(text_so_far="", max_candidates=3)

        # エラーメッセージに文字列長に関する内容が含まれることを確認
        error = exc_info.value.errors()[0]
        assert error["type"] == "string_too_short"
        assert error["loc"] == ("text_so_far",)


class TestPredictionResponse:
    """PredictionResponse モデルのテスト"""
    
    def test_valid_response(self):
        """有効なレスポンスデータでモデルが作成されることを確認"""
        candidates = [
            PredictionCandidate(full_text="test1", answer="answer1", probability=60),
            PredictionCandidate(full_text="test2", answer="answer2", probability=30)
        ]
        
        response = PredictionResponse(
            candidates=candidates,
            total_probability=90,
            text_so_far="test／"
        )
        
        assert len(response.candidates) == 2
        assert response.total_probability == 90
        assert response.text_so_far == "test／"
    
    def test_empty_candidates(self):
        """空の候補リストでもモデルが作成されることを確認"""
        response = PredictionResponse(
            candidates=[],
            total_probability=0,
            text_so_far="test／"
        )
        
        assert len(response.candidates) == 0
        assert response.total_probability == 0
