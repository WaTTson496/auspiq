"""バッチAPI機能のテスト"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from auspiq.api_client import OpenAIClient, BatchAPIError
from auspiq.config import Config
from auspiq.models import QuizQuestion, PredictionCandidate, AnalysisPoint


class TestBatchAPI:
    """バッチAPI機能のテスト"""

    @pytest.fixture
    def config(self):
        """テスト用設定"""
        return Config(
            api_key="test-api-key",
            model="gpt-4",
            max_tokens=2000,
            temperature=0.1
        )

    @pytest.fixture
    def client(self, config):
        """テスト用クライアント"""
        client = OpenAIClient(config)
        # プロパティを回避するために_clientを直接モック
        client._client = MagicMock()
        return client

    @pytest.fixture
    def questions(self):
        """テスト用問題リスト"""
        return [
            QuizQuestion(original_text="静岡県と山梨県の県境に位置する、標高3776mと日本で最も高い山は何でしょう？"),
            QuizQuestion(original_text="電気回路に流れる電流の大きさは、電圧に比例し、電気抵抗に反比例するという物理学の法則を何というでしょう？"),
        ]

    def test_create_batch_requests_single_mode(self, client, questions):
        """単発推測モードでのバッチリクエスト作成テスト"""
        with patch('auspiq.prompts.PromptTemplate.get_prediction_messages') as mock_get_messages:
            mock_get_messages.return_value = [{"role": "user", "content": "test message"}]

            requests = client._create_batch_requests(questions, mode='single', step=1, min_length=1)

            assert len(requests) == 2

            # 最初の問題のリクエストをチェック（実際の中点位置を確認）
            req1 = requests[0]
            question_length = len(questions[0].original_text)  # 39文字
            expected_mid_point = max(1, question_length // 2)  # 19
            assert req1['custom_id'] == f'q0_single_{expected_mid_point}'
            assert req1['method'] == 'POST'
            assert req1['url'] == '/v1/chat/completions'
            assert req1['body']['model'] == 'gpt-4'
            assert 'messages' in req1['body']

    def test_create_batch_requests_full_mode(self, client, questions):
        """全文解析モードでのバッチリクエスト作成テスト"""
        with patch('auspiq.prompts.PromptTemplate.get_prediction_messages') as mock_get_messages:
            mock_get_messages.return_value = [{"role": "user", "content": "test message"}]

            # 短いステップで制限してテスト
            requests = client._create_batch_requests(
                [questions[0]],  # 1つの問題のみ
                mode='full',
                step=10,  # 大きなステップでリクエスト数を減らす
                min_length=5
            )

            # 実際の問題文の長さを確認（39文字）
            question_length = len(questions[0].original_text)  # 39文字
            expected_positions = list(range(5, question_length - 5, 10))  # 5から29まで10文字おき
            assert len(requests) == len(expected_positions)

            # カスタムIDの形式をチェック
            for i, req in enumerate(requests):
                expected_pos = expected_positions[i]
                assert req['custom_id'] == f'q0_full_{expected_pos}'

    @patch('tempfile.NamedTemporaryFile')
    @patch('builtins.open')
    def test_upload_batch_file(self, mock_open, mock_tempfile, client):
        """バッチファイルアップロードテスト"""
        # tempfileのモック設定
        mock_temp_file = MagicMock()
        mock_temp_file.name = '/tmp/test_batch.jsonl'
        mock_tempfile.return_value.__enter__.return_value = mock_temp_file

        # openのモック設定
        mock_file_handle = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file_handle

        # OpenAIクライアントのモック（既にfixtureでmockされている）
        mock_batch_file = MagicMock()
        mock_batch_file.id = 'file-test123'
        client._client.files.create.return_value = mock_batch_file

        batch_requests = [
            {"custom_id": "test1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-4"}}
        ]

        result = client._upload_batch_file(batch_requests)

        assert result == 'file-test123'
        client._client.files.create.assert_called_once()

    def test_create_batch_job(self, client):
        """バッチジョブ作成テスト"""
        mock_batch_job = MagicMock()
        mock_batch_job.id = 'batch-job-123'
        client._client.batches.create.return_value = mock_batch_job

        result = client._create_batch_job('file-123', '24h')

        assert result == 'batch-job-123'
        client._client.batches.create.assert_called_once_with(
            input_file_id='file-123',
            endpoint='/v1/chat/completions',
            completion_window='24h'
        )

    def test_wait_for_batch_completion_success(self, client):
        """バッチジョブ完了待機テスト（成功ケース）"""
        mock_batch_job = MagicMock()
        mock_batch_job.status = 'completed'
        mock_batch_job.output_file_id = 'output-file-123'
        client._client.batches.retrieve.return_value = mock_batch_job

        with patch.object(client, '_download_batch_results') as mock_download:
            mock_download.return_value = [{'custom_id': 'test1', 'response': {'choices': []}}]

            result = client._wait_for_batch_completion('batch-job-123')

            assert len(result) == 1
            mock_download.assert_called_once_with('output-file-123')

    def test_wait_for_batch_completion_failure(self, client):
        """バッチジョブ完了待機テスト（失敗ケース）"""
        mock_batch_job = MagicMock()
        mock_batch_job.status = 'failed'
        mock_batch_job.errors = 'Test error'
        client._client.batches.retrieve.return_value = mock_batch_job

        with pytest.raises(BatchAPIError, match="failed with status: failed"):
            client._wait_for_batch_completion('batch-job-123')

    def test_download_batch_results(self, client):
        """バッチ結果ダウンロードテスト"""
        mock_response = MagicMock()
        mock_response.text = '{"custom_id": "test1", "response": {"choices": []}}\n{"custom_id": "test2", "response": {"choices": []}}\n'
        client._client.files.content.return_value = mock_response

        result = client._download_batch_results('output-file-123')

        assert len(result) == 2
        assert result[0]['custom_id'] == 'test1'
        assert result[1]['custom_id'] == 'test2'

    def test_parse_batch_response(self, client):
        """バッチレスポンス解析テスト"""
        response_data = {
            "choices": [
                {
                    "message": {
                        "content": '{"candidates": [{"full_text": "test question", "answer": "test answer", "probability": 85}], "total_probability": 90}'
                    }
                }
            ]
        }

        result = client._parse_batch_response(response_data, "test text/")

        assert len(result.candidates) == 1
        assert result.candidates[0].full_text == "test question"
        assert result.candidates[0].answer == "test answer"
        assert result.candidates[0].probability == 85
        assert result.total_probability == 90
        assert result.text_so_far == "test text/"

    def test_parse_batch_results_single_mode(self, client, questions):
        """バッチ結果解析テスト（単発推測モード）"""
        # 実際の中点位置を計算
        question_length = len(questions[0].original_text)
        mid_point = max(1, question_length // 2)

        batch_results = [
            {
                "custom_id": f"q0_single_{mid_point}",
                "response": {
                    "choices": [
                        {
                            "message": {
                                "content": '{"candidates": [{"full_text": "test question", "answer": "富士山", "probability": 85}], "total_probability": 90}'
                            }
                        }
                    ]
                }
            }
        ]

        results = client._parse_batch_results(batch_results, [questions[0]], 'single')

        assert len(results) == 1
        assert len(results[0].analysis_points) == 1
        assert results[0].analysis_points[0].position == mid_point
        assert results[0].analysis_points[0].candidates[0].answer == "富士山"

    @patch.object(OpenAIClient, '_create_batch_requests')
    @patch.object(OpenAIClient, '_upload_batch_file')
    @patch.object(OpenAIClient, '_create_batch_job')
    def test_submit_batch_job_integration(self, mock_create_job, mock_upload, mock_create_requests, client, questions):
        """バッチジョブ投入統合テスト"""
        # モックの設定
        mock_create_requests.return_value = [{"custom_id": "test1"}]
        mock_upload.return_value = "file-123"
        mock_create_job.return_value = "batch-job-123"

        result = client.submit_batch_job(
            questions=questions,
            mode='single',
            step=1,
            min_length=1,
            completion_window='24h'
        )

        # すべてのメソッドが呼ばれたことを確認
        mock_create_requests.assert_called_once_with(questions, 'single', 1, 1)
        mock_upload.assert_called_once_with([{"custom_id": "test1"}])
        mock_create_job.assert_called_once_with("file-123", '24h')

        assert result == "batch-job-123"

    def test_get_batch_job_status(self, client):
        """バッチジョブステータス取得テスト"""
        mock_batch_job = MagicMock()
        mock_batch_job.id = 'batch-job-123'
        mock_batch_job.status = 'completed'
        mock_batch_job.created_at = 1640995200  # 2022-01-01 00:00:00
        mock_batch_job.completed_at = 1640998800  # 2022-01-01 01:00:00
        mock_batch_job.request_counts = MagicMock()
        mock_batch_job.request_counts.total = 100
        mock_batch_job.request_counts.completed = 95
        mock_batch_job.request_counts.failed = 5

        client._client.batches.retrieve.return_value = mock_batch_job

        result = client.get_batch_job_status('batch-job-123')

        assert result['id'] == 'batch-job-123'
        assert result['status'] == 'completed'
        assert result['created_at'] == 1640995200
        assert result['completed_at'] == 1640998800
        assert result['request_counts'].total == 100

    def test_retrieve_batch_results_integration(self, client, questions):
        """バッチ結果取得統合テスト"""
        # ステータス取得のモック
        client.get_batch_job_status = MagicMock(return_value={'status': 'completed'})

        # バッチジョブ詳細のモック
        mock_batch_job = MagicMock()
        mock_batch_job.output_file_id = 'output-file-123'
        client._client.batches.retrieve.return_value = mock_batch_job

        # 結果ダウンロードのモック
        client._download_batch_results = MagicMock(return_value=[
            {'custom_id': 'q0_single_19', 'response': {'choices': [{'message': {'content': '{"candidates": [{"full_text": "test", "answer": "test", "probability": 80}], "total_probability": 90}'}}]}}
        ])

        # 結果解析のモック
        client._parse_batch_results = MagicMock(return_value=[])

        result = client.retrieve_batch_results('batch-job-123', questions, 'single')

        # メソッドが呼ばれたことを確認
        client.get_batch_job_status.assert_called_once_with('batch-job-123')
        client._client.batches.retrieve.assert_called_once_with('batch-job-123')
        client._download_batch_results.assert_called_once_with('output-file-123')

        assert result == []