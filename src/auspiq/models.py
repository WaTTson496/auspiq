"""データモデルの定義"""
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class PredictionCandidate(BaseModel):
    """推測候補を表すモデル"""

    full_text: str = Field(..., description="完全な問題文")
    answer: str = Field(..., description="解答")
    probability: int = Field(..., ge=0, le=100, description="蓋然性（0-100%）")

    @field_validator('probability', mode='before')
    @classmethod
    def parse_probability(cls, v):
        """確率値を正規化して整数に変換する"""
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            # "<1%" のような文字列を処理
            if v.strip().lower() in ['<1%', '<1']:
                return 0
            # "5%" のような文字列を処理
            if v.strip().endswith('%'):
                try:
                    return int(float(v.strip()[:-1]))
                except (ValueError, IndexError):
                    return 0
            # 数値文字列を処理
            try:
                return int(float(v))
            except ValueError:
                return 0
        return int(v)


class AnalysisPoint(BaseModel):
    """解析ポイントを表すモデル"""
    
    position: int = Field(..., ge=0, description="文字位置")
    text_so_far: str = Field(..., description="その位置までの問題文")
    candidates: List[PredictionCandidate] = Field(..., description="推測候補リスト")
    total_probability: int = Field(..., ge=0, le=100, description="全候補の合計蓋然性")


class QuizQuestion(BaseModel):
    """クイズ問題を表すモデル"""
    
    original_text: str = Field(..., description="元の問題文")
    correct_answer: Optional[str] = Field(None, description="正解（既知の場合）")


class AnalysisResult(BaseModel):
    """解析結果を表すモデル"""
    
    question: QuizQuestion = Field(..., description="対象の問題")
    analysis_points: List[AnalysisPoint] = Field(..., description="解析ポイントのリスト")


class PredictionRequest(BaseModel):
    """API予測リクエストを表すモデル"""

    text_so_far: str = Field(..., min_length=1, description="問題文の途中まで（空文字不可）")
    max_candidates: int = Field(5, ge=1, le=10, description="最大候補数")


class PredictionResponse(BaseModel):
    """API予測レスポンスを表すモデル"""

    candidates: List[PredictionCandidate] = Field(..., description="推測候補リスト")
    total_probability: int = Field(..., ge=0, le=100, description="全候補の合計蓋然性")
    text_so_far: str = Field(..., description="入力された問題文の途中まで")


class PracticeQuestion(BaseModel):
    """練習用問題を表すモデル"""

    original_text: str = Field(..., description="元の問題文")
    correct_answer: Optional[str] = Field(None, description="正解")
    analysis_points: List[AnalysisPoint] = Field(default_factory=list, description="解析ポイント")


class PracticeAnswer(BaseModel):
    """練習での回答結果を表すモデル"""

    result: str = Field(..., description="結果 (correct/incorrect/skip)")
    user_answer: Optional[str] = Field(None, description="ユーザーの回答")
    push_position: int = Field(..., ge=0, description="押した位置")
    time_taken: float = Field(..., ge=0.0, description="かかった時間（秒）")


class PracticeSession(BaseModel):
    """練習セッションを表すモデル"""

    questions: List[PracticeQuestion] = Field(..., description="練習問題リスト")
    answers: List[PracticeAnswer] = Field(default_factory=list, description="回答結果リスト")
    start_time: Optional[float] = Field(None, description="開始時刻")
    end_time: Optional[float] = Field(None, description="終了時刻")


class PracticeStats(BaseModel):
    """練習統計を表すモデル"""

    total_questions: int = Field(..., ge=0, description="総問題数")
    correct_answers: int = Field(..., ge=0, description="正解数")
    incorrect_answers: int = Field(..., ge=0, description="不正解数")
    skipped_questions: int = Field(..., ge=0, description="スキップ数")
    average_push_position: float = Field(..., ge=0.0, description="平均押しポイント")
    total_time: float = Field(..., ge=0.0, description="総時間")
    accuracy_rate: float = Field(..., ge=0.0, le=100.0, description="正解率")
