"""OpenAI API クライアント"""
import json
from typing import Optional, List, Dict, Any
import time
from pathlib import Path
import tempfile
import uuid

from openai import OpenAI
from openai.types.chat import ChatCompletion
from pydantic import ValidationError

from .config import Config
from .logging_config import get_logger
from .models import PredictionRequest, PredictionResponse, PredictionCandidate, QuizQuestion, AnalysisPoint, AnalysisResult
from .prompts import PromptTemplate


logger = get_logger(__name__)


class APIError(Exception):
    """API関連のエラー"""
    pass


class APIRateLimitError(APIError):
    """APIレート制限エラー"""
    pass


class APIValidationError(APIError):
    """APIレスポンス検証エラー"""
    pass


class BatchAPIError(APIError):
    """バッチAPI関連のエラー"""
    pass


class OpenAIClient:
    """OpenAI API クライアント"""
    
    def __init__(self, config: Config, api_key: Optional[str] = None):
        """
        OpenAI クライアントを初期化する
        
        Args:
            config: アプリケーション設定
            api_key: APIキー（Noneの場合は設定から取得）
        """
        self.config = config
        self._api_key = api_key
        self._client: Optional[OpenAI] = None
        
    @property
    def client(self) -> OpenAI:
        """OpenAI クライアントインスタンスを取得する"""
        if self._client is None:
            api_key = self._api_key or self.config.api_key
            if not api_key:
                raise APIError("OpenAI API key is not configured")
            
            self._client = OpenAI(api_key=api_key)
        return self._client
    
    def predict_quiz_continuation(
        self,
        request: PredictionRequest,
        retry_count: int = 3,
        retry_delay: float = 1.0
    ) -> PredictionResponse:
        """
        クイズ問題文の続きを予測する

        Args:
            request: 予測リクエスト
            retry_count: リトライ回数
            retry_delay: リトライ間隔（秒）

        Returns:
            予測結果

        Raises:
            APIError: API呼び出しエラー
            APIRateLimitError: レート制限エラー
            APIValidationError: レスポンス検証エラー
        """
        # 入力検証
        if not request.text_so_far or not request.text_so_far.strip():
            raise APIValidationError("問題文が空です。問題文の一部を入力してください。")

        messages = PromptTemplate.get_prediction_messages(
            text_so_far=request.text_so_far,
            max_candidates=request.max_candidates
        )
        
        last_exception = None
        
        for attempt in range(retry_count + 1):
            try:
                response = self._make_api_call(messages)
                return self._parse_response(response, request.text_so_far)
                
            except APIRateLimitError as e:
                if attempt < retry_count:
                    logger.warning(f"Rate limit hit, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    last_exception = e
                    continue
                raise e
                
            except APIValidationError as e:
                # Validation errors should not be retried
                raise e
                
            except APIError as e:
                # Some API errors can be retried (like temporary network issues)
                if attempt < retry_count and "authentication" not in str(e).lower() and "not found" not in str(e).lower():
                    logger.warning(f"API error, retrying: {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    last_exception = e
                    continue
                raise e
                
            except Exception as e:
                if attempt < retry_count:
                    logger.warning(f"Unexpected error, retrying: {e}")
                    time.sleep(retry_delay)
                    last_exception = e
                    continue
                raise APIError(f"Failed after {retry_count} retries: {e}")
        
        # This should not be reached, but just in case
        if last_exception:
            raise last_exception
        raise APIError("Unknown error occurred")
    
    def _make_api_call(self, messages: List[dict]) -> ChatCompletion:
        """
        OpenAI API を呼び出す

        Args:
            messages: チャットメッセージリスト

        Returns:
            API レスポンス

        Raises:
            APIError: API呼び出しエラー
            APIRateLimitError: レート制限エラー
        """
        try:
            # モデルに応じて適切なパラメータを使用
            api_params = {
                "model": self.config.model,
                "messages": messages,
                "response_format": {"type": "json_object"}
            }

            # 新しいモデル（o1シリーズ、gpt-5など）では異なるパラメータを使用
            if self.config.model.startswith('o1') or self.config.model.startswith('gpt-5'):
                # これらのモデルは大量の推論トークンを使用するため、完了トークン数を増やす
                api_params["max_completion_tokens"] = max(self.config.max_tokens, 3000)
                logger.debug(f"Using max_completion_tokens={api_params['max_completion_tokens']} for model {self.config.model}")
                # これらのモデルは temperature パラメータの制約がある
                if self.config.model.startswith('gpt-5'):
                    # gpt-5 は temperature=1.0 のみサポート（デフォルト値なので省略）
                    logger.debug("gpt-5 model detected, using default temperature")
                    pass
                # o1シリーズは temperature パラメータをサポートしない
                if self.config.model.startswith('o1'):
                    logger.debug("o1 model detected, temperature parameter not supported")
            else:
                api_params["max_tokens"] = self.config.max_tokens
                api_params["temperature"] = self.config.temperature
                logger.debug(f"Using max_tokens={api_params['max_tokens']}, temperature={api_params['temperature']}")

            # リクエストをログに記録（メッセージ内容は先頭のみ）
            logger.debug(f"Making OpenAI API call with parameters:")
            logger.debug(f"  Model: {api_params['model']}")
            logger.debug(f"  Messages count: {len(messages)}")
            for i, msg in enumerate(messages):
                content_preview = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
                logger.debug(f"  Message {i+1} ({msg['role']}): {content_preview}")
            logger.debug(f"  Other params: {{k: v for k, v in api_params.items() if k not in ['model', 'messages']}}")

            logger.info("Sending request to OpenAI API...")
            response = self.client.chat.completions.create(**api_params)

            # レスポンスをログに記録
            logger.info("Received response from OpenAI API")
            logger.debug(f"Response details:")
            logger.debug(f"  Model used: {response.model}")
            logger.debug(f"  Choices count: {len(response.choices)}")

            if response.usage:
                logger.debug(f"  Token usage:")
                logger.debug(f"    Prompt tokens: {response.usage.prompt_tokens}")
                logger.debug(f"    Completion tokens: {response.usage.completion_tokens}")
                logger.debug(f"    Total tokens: {response.usage.total_tokens}")

                # 推論トークンの詳細（利用可能な場合）
                if hasattr(response.usage, 'completion_tokens_details') and response.usage.completion_tokens_details:
                    details = response.usage.completion_tokens_details
                    if hasattr(details, 'reasoning_tokens') and details.reasoning_tokens:
                        logger.debug(f"    Reasoning tokens: {details.reasoning_tokens}")

            if response.choices:
                choice = response.choices[0]
                logger.debug(f"  Choice 0:")
                logger.debug(f"    Finish reason: {choice.finish_reason}")
                if choice.message.content:
                    content_preview = choice.message.content[:300] + "..." if len(choice.message.content) > 300 else choice.message.content
                    logger.debug(f"    Content preview: {content_preview}")
                else:
                    logger.debug(f"    Content: [EMPTY]")

            return response
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Rate limit errors
            if "rate limit" in error_str or "quota" in error_str:
                raise APIRateLimitError(f"OpenAI API rate limit exceeded: {e}")
            
            # Authentication errors
            if "authentication" in error_str or "unauthorized" in error_str:
                raise APIError(f"OpenAI API authentication failed: {e}")
            
            # Model errors
            if "model" in error_str and "not found" in error_str:
                raise APIError(f"OpenAI model '{self.config.model}' not found: {e}")
            
            # Generic API error
            raise APIError(f"OpenAI API call failed: {e}")
    
    def _parse_response(self, response: ChatCompletion, text_so_far: str) -> PredictionResponse:
        """
        API レスポンスをパースする

        Args:
            response: OpenAI API レスポンス
            text_so_far: 入力された問題文の途中まで

        Returns:
            パース済みレスポンス

        Raises:
            APIValidationError: レスポンス検証エラー
        """
        logger.debug("Starting response parsing...")
        logger.debug(f"Input text_so_far: '{text_so_far}'")

        try:
            # レスポンスからコンテンツを取得
            logger.debug(f"Checking response choices: {len(response.choices) if response.choices else 0} choices")
            if not response.choices:
                logger.error("No choices found in API response")
                raise APIValidationError("No choices in API response")

            content = response.choices[0].message.content
            logger.debug(f"Extracted content from choice 0: {'[EMPTY]' if not content else f'{len(content)} characters'}")

            if content and len(content) > 0:
                # コンテンツの先頭部分をログに記録（デバッグ用）
                content_preview = content[:500] + "..." if len(content) > 500 else content
                logger.debug(f"Response content preview: {content_preview}")

            if not content:
                finish_reason = response.choices[0].finish_reason
                logger.debug(f"Empty content detected. Finish reason: {finish_reason}")

                # max-tokens不足の場合の分かりやすいエラーメッセージ
                if finish_reason == 'length':
                    usage_details = response.usage
                    logger.debug(f"Token limit reached. Usage details available: {bool(usage_details)}")
                    if (usage_details and
                        hasattr(usage_details, 'completion_tokens_details') and
                        usage_details.completion_tokens_details and
                        usage_details.completion_tokens_details.reasoning_tokens > 0):
                        # 推論モデル（gpt-5系）の場合
                        reasoning_tokens = usage_details.completion_tokens_details.reasoning_tokens
                        total_completion_tokens = usage_details.completion_tokens
                        logger.error(f"Token limit exceeded: {reasoning_tokens} reasoning tokens, {total_completion_tokens} total completion tokens")
                        raise APIValidationError(
                            f"API response is empty due to token limit. Model '{self.config.model}' used "
                            f"{reasoning_tokens} reasoning tokens out of {total_completion_tokens} completion tokens, "
                            f"leaving no tokens for output. Consider increasing max-tokens setting."
                        )
                    else:
                        # 従来モデルの場合
                        logger.error("Token limit exceeded for traditional model")
                        raise APIValidationError(
                            f"API response is empty due to token limit. Consider increasing max-tokens setting."
                        )

                # その他の理由による空レスポンス
                logger.error(f"Empty response with finish reason: {finish_reason}")
                raise APIValidationError(f"Empty content in API response from model {self.config.model}. Finish reason: {finish_reason}")

            # JSONをパース
            logger.debug("Parsing JSON response content...")
            try:
                data = json.loads(content)
                logger.debug(f"JSON parsing successful. Response is {type(data)} with {len(data) if isinstance(data, (dict, list)) else 'unknown'} items")
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                content_preview = content[:500] + "..." if len(content) > 500 else content
                logger.debug(f"Invalid JSON content (first 500 chars): {content_preview}")
                raise APIValidationError(f"Invalid JSON in API response: {e}. Content preview: {content[:200]}")

            # レスポンス構造の検証
            logger.debug("Validating response structure...")
            if not isinstance(data, dict):
                logger.error(f"Response is not a JSON object: {type(data)}")
                raise APIValidationError(f"API response is not a JSON object, got: {type(data)}")

            available_fields = list(data.keys())
            logger.debug(f"Available fields in response: {available_fields}")

            if "candidates" not in data:
                logger.error(f"Missing 'candidates' field. Available: {available_fields}")
                raise APIValidationError(f"Missing 'candidates' field in API response. Available fields: {available_fields}")

            if "total_probability" not in data:
                logger.error(f"Missing 'total_probability' field. Available: {available_fields}")
                raise APIValidationError(f"Missing 'total_probability' field in API response. Available fields: {available_fields}")

            # 候補リストの検証とパース
            logger.debug("Parsing and validating candidates...")
            candidates_raw = data["candidates"]
            logger.debug(f"Raw candidates count: {len(candidates_raw) if isinstance(candidates_raw, list) else 'not a list'}")

            candidates = []
            for i, candidate_data in enumerate(candidates_raw):
                logger.debug(f"Processing candidate {i}: {candidate_data}")
                try:
                    candidate = PredictionCandidate(**candidate_data)
                    candidates.append(candidate)
                    logger.debug(f"Candidate {i} parsed successfully: full_text='{candidate.full_text}', probability={candidate.probability}")
                except ValidationError as e:
                    logger.error(f"Candidate {i} validation failed: {e}")
                    logger.debug(f"Invalid candidate data: {candidate_data}")
                    raise APIValidationError(f"Invalid candidate {i}: {e}")

            logger.debug(f"Successfully parsed {len(candidates)} candidates")

            # 全体蓋然性の検証
            logger.debug("Validating total probability...")
            total_probability = data["total_probability"]
            logger.debug(f"Raw total_probability value: {total_probability} (type: {type(total_probability)})")

            if not isinstance(total_probability, int) or not (0 <= total_probability <= 100):
                logger.error(f"Invalid total_probability: {total_probability} (type: {type(total_probability)})")
                raise APIValidationError("Invalid total_probability value")

            logger.debug(f"Total probability validated: {total_probability}%")

            # 最終的なレスポンス作成
            logger.debug("Creating final PredictionResponse object...")
            result = PredictionResponse(
                candidates=candidates,
                total_probability=total_probability,
                text_so_far=text_so_far
            )
            logger.debug(f"Response parsing completed successfully. Created response with {len(result.candidates)} candidates, {result.total_probability}% total probability")

            return result

        except APIValidationError:
            logger.debug("Re-raising APIValidationError")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during response parsing: {e}")
            logger.exception("Full exception details:")
            raise APIValidationError(f"Failed to parse API response: {e}")
    
    def test_connection(self) -> bool:
        """
        API接続をテストする

        Returns:
            接続が成功した場合 True
        """
        try:
            # モデルに応じた簡単なテストリクエストを送信
            if self.config.model.startswith('o1') or self.config.model.startswith('gpt-5'):
                # 新しいモデルはJSON形式を強制しないシンプルなテスト
                api_params = {
                    "model": self.config.model,
                    "messages": [{"role": "user", "content": "Say 'test'"}],
                    "max_completion_tokens": 50  # 推論トークンを考慮して増やす
                }
                response = self.client.chat.completions.create(**api_params)
                # レスポンスがあればOK（コンテンツが空でも接続は成功）
                return bool(response.choices)
            else:
                # 従来のモデルは通常の予測テスト
                test_request = PredictionRequest(
                    text_so_far="テスト／",
                    max_candidates=1
                )
                self.predict_quiz_continuation(test_request)
                return True
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False

    def validate_model(self) -> bool:
        """
        設定されているモデルが有効かどうかをチェックする

        Returns:
            モデルが有効な場合 True
        """
        try:
            # retrieve model endpoint でモデル情報を取得
            self.client.models.retrieve(self.config.model)
            return True
        except Exception as e:
            logger.error(f"Model validation failed for '{self.config.model}': {e}")
            return False

    def submit_batch_job(
        self,
        questions: List[QuizQuestion],
        mode: str = 'single',
        step: int = 1,
        min_length: int = 1,
        completion_window: str = "24h"
    ) -> str:
        """
        OpenAI Batch APIにジョブを投入する（非同期）

        Args:
            questions: 処理する問題のリスト
            mode: 処理モード ('single' または 'full')
            step: 全文解析時のステップ間隔（文字数）
            min_length: 全文解析時の開始最小文字数
            completion_window: 完了期限 ("24h")

        Returns:
            バッチジョブID

        Raises:
            BatchAPIError: バッチAPI処理エラー
        """
        logger.info(f"Submitting batch job for {len(questions)} questions using OpenAI Batch API")
        logger.debug(f"Batch parameters: mode={mode}, step={step}, min_length={min_length}, completion_window={completion_window}")

        try:
            # バッチ用のJSONLファイルを作成
            batch_requests = self._create_batch_requests(questions, mode, step, min_length)
            logger.info(f"Created {len(batch_requests)} batch requests")

            # バッチファイルをアップロード
            batch_file_id = self._upload_batch_file(batch_requests)
            logger.info(f"Uploaded batch file with ID: {batch_file_id}")

            # バッチジョブを作成
            batch_job_id = self._create_batch_job(batch_file_id, completion_window)
            logger.info(f"Created batch job with ID: {batch_job_id}")

            return batch_job_id

        except Exception as e:
            logger.error(f"Batch job submission failed: {e}")
            raise BatchAPIError(f"Batch job submission failed: {e}")

    def get_batch_job_status(self, batch_job_id: str) -> dict:
        """
        バッチジョブのステータスを取得する

        Args:
            batch_job_id: バッチジョブID

        Returns:
            ステータス情報（status, created_at, completed_at, etc.）

        Raises:
            BatchAPIError: バッチAPI処理エラー
        """
        try:
            batch_job = self.client.batches.retrieve(batch_job_id)

            status_info = {
                'id': batch_job.id,
                'status': batch_job.status,
                'created_at': batch_job.created_at,
                'request_counts': batch_job.request_counts if hasattr(batch_job, 'request_counts') else None,
                'metadata': batch_job.metadata if hasattr(batch_job, 'metadata') else None
            }

            if hasattr(batch_job, 'completed_at') and batch_job.completed_at:
                status_info['completed_at'] = batch_job.completed_at

            if hasattr(batch_job, 'failed_at') and batch_job.failed_at:
                status_info['failed_at'] = batch_job.failed_at

            if hasattr(batch_job, 'expired_at') and batch_job.expired_at:
                status_info['expired_at'] = batch_job.expired_at

            if hasattr(batch_job, 'errors') and batch_job.errors:
                status_info['errors'] = batch_job.errors

            return status_info

        except Exception as e:
            logger.error(f"Failed to get batch job status: {e}")
            raise BatchAPIError(f"Failed to get batch job status: {e}")

    def retrieve_batch_results(
        self,
        batch_job_id: str,
        questions: List[QuizQuestion],
        mode: str,
        save_raw_results: bool = False
    ) -> List[AnalysisResult]:
        """
        完了したバッチジョブの結果を取得・解析する

        Args:
            batch_job_id: バッチジョブID
            questions: 元の問題リスト（結果解析用）
            mode: 処理モード ('single' または 'full')
            save_raw_results: デバッグ用にraw結果をファイルに保存するかどうか

        Returns:
            解析結果のリスト

        Raises:
            BatchAPIError: バッチAPI処理エラー
        """
        logger.info(f"Retrieving results for batch job: {batch_job_id}")

        try:
            # ジョブステータスを確認
            status_info = self.get_batch_job_status(batch_job_id)

            if status_info['status'] != 'completed':
                raise BatchAPIError(f"Batch job is not completed. Current status: {status_info['status']}")

            # バッチジョブ詳細を取得して結果ファイルIDを取得
            batch_job = self.client.batches.retrieve(batch_job_id)
            if not hasattr(batch_job, 'output_file_id') or not batch_job.output_file_id:
                raise BatchAPIError("Batch job has no output file")

            # 結果をダウンロード・パース
            batch_results = self._download_batch_results(batch_job.output_file_id)
            logger.info(f"Downloaded {len(batch_results)} batch results")

            # デバッグ用にraw結果を保存（オプショナル）
            if save_raw_results:
                self._save_raw_batch_results(batch_results, batch_job_id)

            # 結果をパース
            analysis_results = self._parse_batch_results(batch_results, questions, mode)
            logger.info(f"Successfully parsed {len(analysis_results)} analysis results")

            return analysis_results

        except Exception as e:
            logger.error(f"Failed to retrieve batch results: {e}")
            raise BatchAPIError(f"Failed to retrieve batch results: {e}")

    def _create_batch_requests(
        self,
        questions: List[QuizQuestion],
        mode: str,
        step: int,
        min_length: int
    ) -> List[Dict[str, Any]]:
        """バッチ用のリクエストリストを作成する"""
        batch_requests = []

        for i, question in enumerate(questions):
            if mode == 'single':
                # 単発推測モード（問題文の中間地点で推測）
                text_length = len(question.original_text)
                mid_point = max(min_length, text_length // 2)
                text_so_far = question.original_text[:mid_point] + "/"

                custom_id = f"q{i}_single_{mid_point}"

                messages = PromptTemplate.get_prediction_messages(
                    text_so_far=text_so_far,
                    max_candidates=5
                )

                batch_request = {
                    "custom_id": custom_id,
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": self.config.model,
                        "messages": messages,
                        "response_format": {"type": "json_object"}
                    }
                }

                # モデル固有のパラメータを設定
                if self.config.model.startswith('o1') or self.config.model.startswith('gpt-5'):
                    batch_request["body"]["max_completion_tokens"] = max(self.config.max_tokens, 3000)
                    if not self.config.model.startswith('o1'):
                        # o1以外では温度設定が可能
                        if not self.config.model.startswith('gpt-5'):
                            batch_request["body"]["temperature"] = self.config.temperature
                else:
                    batch_request["body"]["max_tokens"] = self.config.max_tokens
                    batch_request["body"]["temperature"] = self.config.temperature

                batch_requests.append(batch_request)

            else:
                # 全文解析モード
                text_length = len(question.original_text)

                for pos in range(min_length, text_length - 5, step):
                    text_so_far = question.original_text[:pos] + "/"
                    custom_id = f"q{i}_full_{pos}"

                    messages = PromptTemplate.get_prediction_messages(
                        text_so_far=text_so_far,
                        max_candidates=5
                    )

                    batch_request = {
                        "custom_id": custom_id,
                        "method": "POST",
                        "url": "/v1/chat/completions",
                        "body": {
                            "model": self.config.model,
                            "messages": messages,
                            "response_format": {"type": "json_object"}
                        }
                    }

                    # モデル固有のパラメータを設定
                    if self.config.model.startswith('o1') or self.config.model.startswith('gpt-5'):
                        batch_request["body"]["max_completion_tokens"] = max(self.config.max_tokens, 3000)
                        if not self.config.model.startswith('o1'):
                            if not self.config.model.startswith('gpt-5'):
                                batch_request["body"]["temperature"] = self.config.temperature
                    else:
                        batch_request["body"]["max_tokens"] = self.config.max_tokens
                        batch_request["body"]["temperature"] = self.config.temperature

                    batch_requests.append(batch_request)

        return batch_requests

    def _upload_batch_file(self, batch_requests: List[Dict[str, Any]]) -> str:
        """バッチファイルをOpenAIにアップロードする"""
        # 一時ファイルにJSONLを書き込み
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for request in batch_requests:
                f.write(json.dumps(request) + '\n')
            temp_file_path = f.name

        try:
            # ファイルをアップロード
            with open(temp_file_path, 'rb') as f:
                batch_file = self.client.files.create(
                    file=f,
                    purpose="batch"
                )
            return batch_file.id
        finally:
            # 一時ファイルを削除
            Path(temp_file_path).unlink(missing_ok=True)

    def _create_batch_job(self, batch_file_id: str, completion_window: str) -> str:
        """バッチジョブを作成する"""
        batch_job = self.client.batches.create(
            input_file_id=batch_file_id,
            endpoint="/v1/chat/completions",
            completion_window=completion_window
        )
        return batch_job.id

    def _wait_for_batch_completion(self, batch_job_id: str) -> List[Dict[str, Any]]:
        """バッチジョブの完了を待機し、結果を取得する"""
        logger.info("Waiting for batch job completion...")

        # ポーリング間隔（秒）
        polling_interval = 60
        max_wait_time = 24 * 60 * 60  # 24時間
        elapsed_time = 0

        while elapsed_time < max_wait_time:
            # バッチジョブのステータスを確認
            batch_job = self.client.batches.retrieve(batch_job_id)
            logger.debug(f"Batch job status: {batch_job.status}")

            if batch_job.status == "completed":
                logger.info("Batch job completed successfully")
                # 結果ファイルをダウンロード
                return self._download_batch_results(batch_job.output_file_id)

            elif batch_job.status in ["failed", "expired", "cancelled"]:
                error_msg = f"Batch job {batch_job_id} failed with status: {batch_job.status}"
                if hasattr(batch_job, 'errors') and batch_job.errors:
                    error_msg += f", errors: {batch_job.errors}"
                raise BatchAPIError(error_msg)

            # 進行中の場合は待機
            logger.debug(f"Batch job still in progress, waiting {polling_interval} seconds...")
            time.sleep(polling_interval)
            elapsed_time += polling_interval

        raise BatchAPIError(f"Batch job {batch_job_id} timed out after {max_wait_time} seconds")

    def _download_batch_results(self, output_file_id: str) -> List[Dict[str, Any]]:
        """バッチ結果ファイルをダウンロードしてパースする"""
        try:
            # 結果ファイルの内容を取得
            file_response = self.client.files.content(output_file_id)

            # JSONLをパース
            results = []
            for line in file_response.text.strip().split('\n'):
                if line.strip():
                    results.append(json.loads(line))

            logger.info(f"Downloaded and parsed {len(results)} batch results")
            return results

        except Exception as e:
            raise BatchAPIError(f"Failed to download batch results: {e}")

    def _save_raw_batch_results(self, batch_results: List[Dict[str, Any]], batch_id: str) -> None:
        """デバッグ用にraw batch resultsを保存する"""
        import os
        from datetime import datetime

        try:
            # logsディレクトリが存在することを確認
            logs_dir = "logs"
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)

            # ファイル名を生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"raw_batch_results_{batch_id}_{timestamp}.json"
            filepath = os.path.join(logs_dir, filename)

            # JSONファイルとして保存
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(batch_results, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved raw batch results to {filepath}")

        except Exception as e:
            logger.warning(f"Failed to save raw batch results: {e}")

    def _parse_batch_results(
        self,
        batch_results: List[Dict[str, Any]],
        questions: List[QuizQuestion],
        mode: str
    ) -> List[AnalysisResult]:
        """バッチ結果を解析結果に変換する"""
        # custom_id をキーとする結果辞書を作成
        results_by_id = {}
        for result in batch_results:
            custom_id = result.get("custom_id")
            if custom_id and result.get("response"):
                results_by_id[custom_id] = result["response"]

        analysis_results = []

        for i, question in enumerate(questions):
            analysis_points = []

            if mode == 'single':
                # 単発推測の結果を取得
                text_length = len(question.original_text)
                mid_point = max(1, text_length // 2)
                custom_id = f"q{i}_single_{mid_point}"

                if custom_id in results_by_id:
                    response_data = results_by_id[custom_id]
                    text_so_far = question.original_text[:mid_point] + "/"

                    try:
                        prediction_response = self._parse_batch_response(response_data, text_so_far)
                        analysis_point = AnalysisPoint(
                            position=mid_point,
                            text_so_far=text_so_far,
                            candidates=prediction_response.candidates,
                            total_probability=prediction_response.total_probability
                        )
                        analysis_points.append(analysis_point)
                    except Exception as e:
                        logger.warning(f"Failed to parse result for question {i}, position {mid_point}: {e}")

            else:
                # 全文解析の結果を取得
                text_length = len(question.original_text)

                # ポジション順に並べるために、結果を収集してからソート
                position_results = []
                for pos in range(1, text_length - 5, 1):
                    custom_id = f"q{i}_full_{pos}"
                    if custom_id in results_by_id:
                        position_results.append((pos, custom_id))

                # ポジション順にソート
                position_results.sort(key=lambda x: x[0])

                for pos, custom_id in position_results:
                    response_data = results_by_id[custom_id]
                    text_so_far = question.original_text[:pos] + "/"

                    try:
                        prediction_response = self._parse_batch_response(response_data, text_so_far)
                        analysis_point = AnalysisPoint(
                            position=pos,
                            text_so_far=text_so_far,
                            candidates=prediction_response.candidates,
                            total_probability=prediction_response.total_probability
                        )
                        analysis_points.append(analysis_point)
                    except Exception as e:
                        logger.warning(f"Failed to parse result for question {i}, position {pos}: {e}")

            # 解析結果を作成
            result = AnalysisResult(
                question=question,
                analysis_points=analysis_points
            )
            analysis_results.append(result)

        return analysis_results

    def _parse_batch_response(self, response_data: Dict[str, Any], text_so_far: str) -> PredictionResponse:
        """バッチAPIレスポンスをPredictionResponseに変換する"""
        try:
            # バッチAPIの場合は body の中に choices がある、そうでなければ直接 choices
            if "body" in response_data:
                # 実際のバッチAPI結果の場合
                body = response_data.get("body", {})
                choices = body.get("choices", [])
            else:
                # テストや直接のAPI結果の場合
                choices = response_data.get("choices", [])

            if not choices:
                raise APIValidationError("No choices in batch response")

            content = choices[0].get("message", {}).get("content")
            if not content:
                raise APIValidationError("Empty content in batch response")

            # JSONをパース
            data = json.loads(content)

            # レスポンス構造の検証
            if not isinstance(data, dict) or "candidates" not in data or "total_probability" not in data:
                raise APIValidationError("Invalid response structure in batch result")

            # 候補をパース
            candidates = []
            for candidate_data in data["candidates"]:
                candidate = PredictionCandidate(**candidate_data)
                candidates.append(candidate)

            return PredictionResponse(
                candidates=candidates,
                total_probability=data["total_probability"],
                text_so_far=text_so_far
            )

        except Exception as e:
            raise APIValidationError(f"Failed to parse batch response: {e}")
