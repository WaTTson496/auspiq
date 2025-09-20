"""練習機能のテスト"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from rich.console import Console

from src.auspiq.practice import PracticeEngine
from src.auspiq.models import (
    PracticeQuestion,
    PracticeAnswer,
    PracticeSession,
    PracticeStats,
    AnalysisPoint,
    PredictionCandidate
)


class TestPracticeEngine:
    """PracticeEngineのテストクラス"""

    def test_init(self):
        """初期化のテスト"""
        console = Console()
        engine = PracticeEngine(console)

        assert engine.console == console
        assert engine.session is None
        assert engine.current_question_index == 0
        assert engine.current_position == 0
        assert not engine.is_paused
        assert not engine.is_stopped
        assert engine.auto_pause_threshold == 80
        assert engine.display_speed == 0.1

    def test_init_without_console(self):
        """コンソール無しでの初期化のテスト"""
        engine = PracticeEngine()
        assert engine.console is not None
        assert isinstance(engine.console, Console)

    def test_set_auto_pause_threshold(self):
        """自動一時停止閾値設定のテスト"""
        engine = PracticeEngine()

        engine.set_auto_pause_threshold(90)
        assert engine.auto_pause_threshold == 90

        engine.set_auto_pause_threshold(0)
        assert engine.auto_pause_threshold == 0

    def test_set_display_speed(self):
        """表示速度設定のテスト"""
        engine = PracticeEngine()

        engine.set_display_speed(0.05)
        assert engine.display_speed == 0.05

        # 最小値のテスト
        engine.set_display_speed(0.001)
        assert engine.display_speed == 0.01

        engine.set_display_speed(-1.0)
        assert engine.display_speed == 0.01

    def test_should_auto_pause(self):
        """自動一時停止判定のテスト"""
        engine = PracticeEngine()
        engine.set_auto_pause_threshold(80)

        # テスト用の問題
        question = PracticeQuestion(
            original_text="テスト問題です",
            analysis_points=[
                AnalysisPoint(
                    position=5,
                    text_so_far="テスト問",
                    candidates=[],
                    total_probability=85
                ),
                AnalysisPoint(
                    position=10,
                    text_so_far="テスト問題です",
                    candidates=[],
                    total_probability=70
                )
            ]
        )

        # 位置5で閾値を超える
        assert engine._should_auto_pause(question, 5)

        # 位置6では該当する解析ポイントがない
        assert not engine._should_auto_pause(question, 6)

        # 位置10では閾値を超えない
        assert not engine._should_auto_pause(question, 10)

        # 位置4では該当する解析ポイントがない
        assert not engine._should_auto_pause(question, 4)

    def test_calculate_stats_empty_session(self):
        """空セッションの統計計算テスト"""
        engine = PracticeEngine()
        stats = engine._calculate_stats()

        assert stats.total_questions == 0
        assert stats.correct_answers == 0
        assert stats.incorrect_answers == 0
        assert stats.skipped_questions == 0
        assert stats.average_push_position == 0.0
        assert stats.total_time == 0.0
        assert stats.accuracy_rate == 0.0

    def test_calculate_stats_with_answers(self):
        """回答ありセッションの統計計算テスト"""
        engine = PracticeEngine()

        # セッションを作成
        questions = [
            PracticeQuestion(original_text="問題1"),
            PracticeQuestion(original_text="問題2"),
            PracticeQuestion(original_text="問題3")
        ]
        engine.session = PracticeSession(
            questions=questions,
            start_time=1000.0,
            end_time=1100.0,
            answers=[
                PracticeAnswer(result='correct', user_answer=None, push_position=10, time_taken=5.0),
                PracticeAnswer(result='incorrect', user_answer='間違い', push_position=15, time_taken=7.0),
                PracticeAnswer(result='skip', user_answer=None, push_position=0, time_taken=2.0)
            ]
        )

        stats = engine._calculate_stats()

        assert stats.total_questions == 3
        assert stats.correct_answers == 1
        assert stats.incorrect_answers == 1
        assert stats.skipped_questions == 1
        assert stats.average_push_position == (10 + 15 + 0) / 3
        assert stats.total_time == 100.0
        assert stats.accuracy_rate == pytest.approx(33.33, rel=1e-2)

    @patch('builtins.input')
    @patch('time.sleep')
    def test_record_answer(self, mock_sleep, mock_input):
        """回答記録のテスト"""
        engine = PracticeEngine()
        engine.session = PracticeSession(questions=[])
        engine._question_start_time = 1000.0

        # 時刻をモック
        with patch('time.time', return_value=1005.0):
            engine.current_position = 10
            engine._record_answer('correct', None)

        assert len(engine.session.answers) == 1
        answer = engine.session.answers[0]
        assert answer.result == 'correct'
        assert answer.user_answer is None
        assert answer.push_position == 10
        assert answer.time_taken == 5.0

    @patch('builtins.input')
    @patch('time.sleep')
    def test_record_skip(self, mock_sleep, mock_input):
        """スキップ記録のテスト"""
        engine = PracticeEngine()
        engine.session = PracticeSession(questions=[])
        engine._question_start_time = 1000.0

        with patch('time.time', return_value=1003.0):
            engine.current_position = 5
            engine._record_skip()

        assert len(engine.session.answers) == 1
        answer = engine.session.answers[0]
        assert answer.result == 'skip'
        assert answer.user_answer is None
        assert answer.push_position == 5
        assert answer.time_taken == 3.0


class TestPracticeModels:
    """練習用データモデルのテスト"""

    def test_practice_question_creation(self):
        """PracticeQuestion作成のテスト"""
        question = PracticeQuestion(
            original_text="テスト問題",
            correct_answer="テスト解答",
            analysis_points=[]
        )

        assert question.original_text == "テスト問題"
        assert question.correct_answer == "テスト解答"
        assert question.analysis_points == []

    def test_practice_question_without_answer(self):
        """正解なしのPracticeQuestion作成のテスト"""
        question = PracticeQuestion(
            original_text="テスト問題"
        )

        assert question.original_text == "テスト問題"
        assert question.correct_answer is None
        assert question.analysis_points == []

    def test_practice_answer_creation(self):
        """PracticeAnswer作成のテスト"""
        answer = PracticeAnswer(
            result="correct",
            user_answer="正解",
            push_position=15,
            time_taken=5.5
        )

        assert answer.result == "correct"
        assert answer.user_answer == "正解"
        assert answer.push_position == 15
        assert answer.time_taken == 5.5

    def test_practice_session_creation(self):
        """PracticeSession作成のテスト"""
        questions = [
            PracticeQuestion(original_text="問題1"),
            PracticeQuestion(original_text="問題2")
        ]

        session = PracticeSession(
            questions=questions,
            start_time=1000.0
        )

        assert len(session.questions) == 2
        assert session.answers == []
        assert session.start_time == 1000.0
        assert session.end_time is None

    def test_practice_stats_creation(self):
        """PracticeStats作成のテスト"""
        stats = PracticeStats(
            total_questions=10,
            correct_answers=7,
            incorrect_answers=2,
            skipped_questions=1,
            average_push_position=12.5,
            total_time=60.0,
            accuracy_rate=70.0
        )

        assert stats.total_questions == 10
        assert stats.correct_answers == 7
        assert stats.incorrect_answers == 2
        assert stats.skipped_questions == 1
        assert stats.average_push_position == 12.5
        assert stats.total_time == 60.0
        assert stats.accuracy_rate == 70.0

    def test_practice_stats_validation(self):
        """PracticeStats バリデーションのテスト"""
        # 正解率が100%を超える場合
        with pytest.raises(ValueError):
            PracticeStats(
                total_questions=10,
                correct_answers=7,
                incorrect_answers=2,
                skipped_questions=1,
                average_push_position=12.5,
                total_time=60.0,
                accuracy_rate=150.0
            )

        # 負の値の場合
        with pytest.raises(ValueError):
            PracticeStats(
                total_questions=-1,
                correct_answers=7,
                incorrect_answers=2,
                skipped_questions=1,
                average_push_position=12.5,
                total_time=60.0,
                accuracy_rate=70.0
            )