"""OpenAI API クライアントのテスト"""
import json
import pytest
from unittest.mock import Mock, patch
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from auspiq.api_client import (
    OpenAIClient,
    APIError,
    APIRateLimitError,
    APIValidationError
)
from auspiq.config import Config
from auspiq.models import PredictionRequest, PredictionResponse


class TestOpenAIClient:
    """OpenAI クライアントのテストクラス"""
    
    @pytest.fixture
    def config(self):
        """テスト用設定"""
        return Config(
            api_key="test-api-key",
            model="gpt-4",
            max_tokens=1000,
            temperature=0.1
        )
    
    @pytest.fixture
    def client(self, config):
        """テスト用クライアント"""
        return OpenAIClient(config)
    
    @pytest.fixture
    def sample_request(self):
        """テスト用リクエスト"""
        return PredictionRequest(
            text_so_far="静岡県と山梨県の県境に位置する、標高／",
            max_candidates=3
        )
    
    @pytest.fixture
    def sample_api_response(self):
        """テスト用API レスポンス"""
        response_content = {
            "candidates": [
                {
                    "full_text": "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？",
                    "answer": "富士山",
                    "probability": 85
                },
                {
                    "full_text": "静岡県と山梨県の県境に位置する、標高3000m級の火山は何でしょう？",
                    "answer": "富士山",
                    "probability": 10
                }
            ],
            "total_probability": 95,
            "text_so_far": "静岡県と山梨県の県境に位置する、標高／"
        }
        
        # ChatCompletion オブジェクトを作成
        message = ChatCompletionMessage(
            role="assistant",
            content=json.dumps(response_content, ensure_ascii=False)
        )
        choice = Choice(
            index=0,
            message=message,
            finish_reason="stop"
        )
        
        return ChatCompletion(
            id="test-completion",
            choices=[choice],
            created=1234567890,
            model="gpt-4",
            object="chat.completion"
        )
    
    def test_client_initialization_with_api_key(self, config):
        """API キー付きでクライアントが初期化されることを確認"""
        client = OpenAIClient(config, api_key="custom-key")
        assert client._api_key == "custom-key"
        assert client.config == config
    
    def test_client_initialization_without_api_key(self, config):
        """API キーなしでクライアントが初期化されることを確認"""
        client = OpenAIClient(config)
        assert client._api_key is None
        assert client.config == config
    
    def test_client_property_with_config_api_key(self, client):
        """設定からAPI キーを取得してクライアントが作成されることを確認"""
        with patch('auspiq.api_client.OpenAI') as mock_openai:
            _ = client.client
            mock_openai.assert_called_once_with(api_key="test-api-key")
    
    def test_client_property_without_api_key(self):
        """API キーが設定されていない場合にエラーが発生することを確認"""
        config = Config(api_key=None)
        client = OpenAIClient(config)
        
        with pytest.raises(APIError, match="OpenAI API key is not configured"):
            _ = client.client
    
    @patch('auspiq.api_client.OpenAI')
    def test_predict_quiz_continuation_success(self, mock_openai, client, sample_request, sample_api_response):
        """クイズ続き予測が成功することを確認"""
        # OpenAI クライアントをモック
        mock_client_instance = Mock()
        mock_openai.return_value = mock_client_instance
        mock_client_instance.chat.completions.create.return_value = sample_api_response
        
        result = client.predict_quiz_continuation(sample_request)
        
        # 結果の検証
        assert isinstance(result, PredictionResponse)
        assert len(result.candidates) == 2
        assert result.total_probability == 95
        assert result.text_so_far == "静岡県と山梨県の県境に位置する、標高／"
        
        # 最初の候補の検証
        first_candidate = result.candidates[0]
        assert first_candidate.answer == "富士山"
        assert first_candidate.probability == 85
        
        # API呼び出しパラメータの検証
        mock_client_instance.chat.completions.create.assert_called_once()
        call_args = mock_client_instance.chat.completions.create.call_args
        assert call_args[1]['model'] == "gpt-4"
        assert call_args[1]['max_tokens'] == 1000
        assert call_args[1]['temperature'] == 0.1
        assert call_args[1]['response_format'] == {"type": "json_object"}
    
    @patch('auspiq.api_client.OpenAI')
    def test_predict_quiz_continuation_rate_limit_error(self, mock_openai, client, sample_request):
        """レート制限エラーが適切に処理されることを確認"""
        mock_client_instance = Mock()
        mock_openai.return_value = mock_client_instance
        mock_client_instance.chat.completions.create.side_effect = Exception("rate limit exceeded")
        
        with pytest.raises(APIRateLimitError):
            client.predict_quiz_continuation(sample_request, retry_count=0)
    
    @patch('auspiq.api_client.OpenAI')
    def test_predict_quiz_continuation_authentication_error(self, mock_openai, client, sample_request):
        """認証エラーが適切に処理されることを確認"""
        mock_client_instance = Mock()
        mock_openai.return_value = mock_client_instance
        mock_client_instance.chat.completions.create.side_effect = Exception("authentication failed")
        
        with pytest.raises(APIError, match="OpenAI API authentication failed"):
            client.predict_quiz_continuation(sample_request, retry_count=0)
    
    @patch('auspiq.api_client.OpenAI')
    def test_predict_quiz_continuation_model_not_found(self, mock_openai, client, sample_request):
        """モデルが見つからないエラーが適切に処理されることを確認"""
        mock_client_instance = Mock()
        mock_openai.return_value = mock_client_instance
        mock_client_instance.chat.completions.create.side_effect = Exception("model not found")
        
        with pytest.raises(APIError, match="OpenAI model 'gpt-4' not found"):
            client.predict_quiz_continuation(sample_request, retry_count=0)
    
    @patch('auspiq.api_client.OpenAI')
    @patch('auspiq.api_client.time.sleep')
    def test_predict_quiz_continuation_retry_mechanism(self, mock_sleep, mock_openai, client, sample_request, sample_api_response):
        """リトライ機能が正常に動作することを確認"""
        mock_client_instance = Mock()
        mock_openai.return_value = mock_client_instance
        
        # 最初の呼び出しで例外、2回目で成功
        mock_client_instance.chat.completions.create.side_effect = [
            Exception("temporary error"),
            sample_api_response
        ]
        
        result = client.predict_quiz_continuation(sample_request, retry_count=1)
        
        # 成功することを確認
        assert isinstance(result, PredictionResponse)
        
        # リトライが発生したことを確認
        assert mock_client_instance.chat.completions.create.call_count == 2
        mock_sleep.assert_called_once()
    
    def test_parse_response_success(self, client, sample_api_response):
        """レスポンスパースが成功することを確認"""
        text_so_far = "静岡県と山梨県の県境に位置する、標高／"
        result = client._parse_response(sample_api_response, text_so_far)
        
        assert isinstance(result, PredictionResponse)
        assert len(result.candidates) == 2
        assert result.total_probability == 95
        assert result.text_so_far == text_so_far
    
    def test_parse_response_no_choices(self, client):
        """選択肢がないレスポンスでエラーが発生することを確認"""
        response = ChatCompletion(
            id="test",
            choices=[],
            created=1234567890,
            model="gpt-4",
            object="chat.completion"
        )
        
        with pytest.raises(APIValidationError, match="No choices in API response"):
            client._parse_response(response, "test")
    
    def test_parse_response_empty_content(self, client):
        """空のコンテンツでエラーが発生することを確認"""
        message = ChatCompletionMessage(role="assistant", content=None)
        choice = Choice(index=0, message=message, finish_reason="stop")
        response = ChatCompletion(
            id="test",
            choices=[choice],
            created=1234567890,
            model="gpt-4",
            object="chat.completion"
        )
        
        with pytest.raises(APIValidationError, match="Empty content in API response"):
            client._parse_response(response, "test")
    
    def test_parse_response_invalid_json(self, client):
        """無効なJSONでエラーが発生することを確認"""
        message = ChatCompletionMessage(role="assistant", content="invalid json")
        choice = Choice(index=0, message=message, finish_reason="stop")
        response = ChatCompletion(
            id="test",
            choices=[choice],
            created=1234567890,
            model="gpt-4",
            object="chat.completion"
        )
        
        with pytest.raises(APIValidationError, match="Invalid JSON in API response"):
            client._parse_response(response, "test")
    
    def test_parse_response_missing_candidates(self, client):
        """candidatesフィールドがないレスポンスでエラーが発生することを確認"""
        content = {"total_probability": 95}
        message = ChatCompletionMessage(
            role="assistant", 
            content=json.dumps(content)
        )
        choice = Choice(index=0, message=message, finish_reason="stop")
        response = ChatCompletion(
            id="test",
            choices=[choice],
            created=1234567890,
            model="gpt-4",
            object="chat.completion"
        )
        
        with pytest.raises(APIValidationError, match="Missing 'candidates' field"):
            client._parse_response(response, "test")
    
    def test_parse_response_invalid_candidate(self, client):
        """無効な候補データでエラーが発生することを確認"""
        content = {
            "candidates": [
                {"full_text": "test", "answer": "test"}  # probability missing
            ],
            "total_probability": 95
        }
        message = ChatCompletionMessage(
            role="assistant", 
            content=json.dumps(content)
        )
        choice = Choice(index=0, message=message, finish_reason="stop")
        response = ChatCompletion(
            id="test",
            choices=[choice],
            created=1234567890,
            model="gpt-4",
            object="chat.completion"
        )
        
        with pytest.raises(APIValidationError, match="Invalid candidate 0"):
            client._parse_response(response, "test")
    
    @patch('auspiq.api_client.OpenAI')
    def test_test_connection_success(self, mock_openai, client, sample_api_response):
        """接続テストが成功することを確認"""
        mock_client_instance = Mock()
        mock_openai.return_value = mock_client_instance
        mock_client_instance.chat.completions.create.return_value = sample_api_response
        
        result = client.test_connection()
        assert result is True
    
    @patch('auspiq.api_client.OpenAI')
    def test_test_connection_failure(self, mock_openai, client):
        """接続テストが失敗することを確認"""
        mock_client_instance = Mock()
        mock_openai.return_value = mock_client_instance
        mock_client_instance.chat.completions.create.side_effect = Exception("connection failed")

        result = client.test_connection()
        assert result is False

    @patch('auspiq.api_client.OpenAI')
    def test_validate_model_success(self, mock_openai, client):
        """モデル検証が成功することを確認"""
        mock_client_instance = Mock()
        mock_openai.return_value = mock_client_instance
        # retrieve model が正常に応答するモック
        mock_client_instance.models.retrieve.return_value = {"id": "gpt-4", "object": "model"}

        result = client.validate_model()
        assert result is True
        mock_client_instance.models.retrieve.assert_called_once_with("gpt-4")

    @patch('auspiq.api_client.OpenAI')
    def test_validate_model_failure(self, mock_openai, client):
        """モデル検証が失敗することを確認"""
        mock_client_instance = Mock()
        mock_openai.return_value = mock_client_instance
        # retrieve model でモデルが見つからない場合の例外
        mock_client_instance.models.retrieve.side_effect = Exception("Model not found")

        result = client.validate_model()
        assert result is False
        mock_client_instance.models.retrieve.assert_called_once_with("gpt-4")

    def test_input_validation_empty_text(self, client):
        """空の問題文で入力検証エラーが発生することを確認"""
        # 空白のみの問題文
        request = PredictionRequest(text_so_far="   ", max_candidates=3)

        with pytest.raises(APIValidationError, match="問題文が空です"):
            client.predict_quiz_continuation(request)

    def test_input_validation_whitespace_text(self, client):
        """空白のみの問題文で入力検証エラーが発生することを確認"""
        request = PredictionRequest(text_so_far="\t\n  ", max_candidates=3)

        with pytest.raises(APIValidationError, match="問題文が空です"):
            client.predict_quiz_continuation(request)

    def test_short_text_processing(self, client):
        """短い問題文でも正常に処理されることを確認（早押しでは実際にありうる）"""
        # 短い問題文（1文字）
        request = PredictionRequest(text_so_far="静/", max_candidates=3)

        # API呼び出しをモックして成功させる
        with patch.object(client, '_make_api_call') as mock_api:
            mock_response = self._create_sample_response()
            mock_api.return_value = mock_response

            result = client.predict_quiz_continuation(request)

            # 正常に処理されることを確認
            assert isinstance(result, PredictionResponse)
            mock_api.assert_called_once()

    def _create_sample_response(self):
        """テスト用のサンプルレスポンスを作成"""
        json_content = json.dumps({
            "candidates": [
                {
                    "full_text": "静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？",
                    "answer": "富士山",
                    "probability": 25
                }
            ],
            "total_probability": 25,
            "text_so_far": "静/"
        })

        message = ChatCompletionMessage(role="assistant", content=json_content)
        choice = Choice(index=0, message=message, finish_reason="stop")
        return ChatCompletion(
            id="test",
            choices=[choice],
            created=1234567890,
            model="gpt-4",
            object="chat.completion"
        )
