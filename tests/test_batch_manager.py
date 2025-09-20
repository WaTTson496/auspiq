"""バッチジョブ管理機能のテスト"""
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from auspiq.batch_manager import BatchJobManager, BatchJobInfo


class TestBatchJobManager:
    """バッチジョブ管理機能のテスト"""

    @pytest.fixture
    def temp_jobs_file(self):
        """一時的なジョブファイル"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        yield temp_path
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def job_manager(self, temp_jobs_file):
        """テスト用ジョブマネージャー"""
        return BatchJobManager(temp_jobs_file)

    @pytest.fixture
    def sample_job_info(self):
        """サンプルジョブ情報"""
        return BatchJobInfo(
            job_id="batch-test-123",
            input_file="/path/to/questions.txt",
            mode="single",
            step=1,
            min_length=1,
            questions_count=10,
            created_at=datetime.now().isoformat(),
            status="submitted"
        )

    def test_save_and_load_job(self, job_manager, sample_job_info):
        """ジョブ保存・読み込みテスト"""
        # ジョブを保存
        job_manager.save_job(sample_job_info)

        # ジョブを読み込み
        loaded_job = job_manager.get_job(sample_job_info.job_id)

        assert loaded_job is not None
        assert loaded_job.job_id == sample_job_info.job_id
        assert loaded_job.input_file == sample_job_info.input_file
        assert loaded_job.mode == sample_job_info.mode
        assert loaded_job.questions_count == sample_job_info.questions_count
        assert loaded_job.status == sample_job_info.status

    def test_get_nonexistent_job(self, job_manager):
        """存在しないジョブ取得テスト"""
        result = job_manager.get_job("nonexistent-job-id")
        assert result is None

    def test_update_job_status(self, job_manager, sample_job_info):
        """ジョブステータス更新テスト"""
        # ジョブを保存
        job_manager.save_job(sample_job_info)

        # ステータスを更新
        job_manager.update_job_status(sample_job_info.job_id, "completed", output_file="results.json")

        # 更新されたジョブを取得
        updated_job = job_manager.get_job(sample_job_info.job_id)

        assert updated_job.status == "completed"
        assert updated_job.output_file == "results.json"
        assert updated_job.completed_at is not None

    def test_list_jobs(self, job_manager):
        """ジョブ一覧取得テスト"""
        # 複数のジョブを作成
        jobs = []
        for i in range(5):
            job = BatchJobInfo(
                job_id=f"batch-test-{i}",
                input_file=f"/path/to/questions{i}.txt",
                mode="single",
                step=1,
                min_length=1,
                questions_count=10,
                created_at=(datetime.now() - timedelta(hours=i)).isoformat(),
                status="submitted"
            )
            jobs.append(job)
            job_manager.save_job(job)

        # ジョブ一覧を取得
        job_list = job_manager.list_jobs()

        assert len(job_list) == 5

        # 作成日時で降順ソートされていることを確認
        for i in range(1, len(job_list)):
            prev_time = datetime.fromisoformat(job_list[i-1].created_at)
            curr_time = datetime.fromisoformat(job_list[i].created_at)
            assert prev_time >= curr_time

    def test_list_jobs_with_limit(self, job_manager):
        """制限付きジョブ一覧取得テスト"""
        # 5つのジョブを作成
        for i in range(5):
            job = BatchJobInfo(
                job_id=f"batch-test-{i}",
                input_file=f"/path/to/questions{i}.txt",
                mode="single",
                step=1,
                min_length=1,
                questions_count=10,
                created_at=datetime.now().isoformat(),
                status="submitted"
            )
            job_manager.save_job(job)

        # 上位3つのみ取得
        job_list = job_manager.list_jobs(limit=3)

        assert len(job_list) == 3

    def test_delete_job(self, job_manager, sample_job_info):
        """ジョブ削除テスト"""
        # ジョブを保存
        job_manager.save_job(sample_job_info)

        # ジョブが存在することを確認
        assert job_manager.get_job(sample_job_info.job_id) is not None

        # ジョブを削除
        result = job_manager.delete_job(sample_job_info.job_id)
        assert result is True

        # ジョブが削除されたことを確認
        assert job_manager.get_job(sample_job_info.job_id) is None

    def test_delete_nonexistent_job(self, job_manager):
        """存在しないジョブ削除テスト"""
        result = job_manager.delete_job("nonexistent-job-id")
        assert result is False

    def test_cleanup_old_jobs(self, job_manager):
        """古いジョブクリーンアップテスト"""
        # 古いジョブを作成
        old_job = BatchJobInfo(
            job_id="batch-old-123",
            input_file="/path/to/questions.txt",
            mode="single",
            step=1,
            min_length=1,
            questions_count=10,
            created_at=(datetime.now() - timedelta(days=35)).isoformat(),  # 35日前
            status="completed"
        )

        # 新しいジョブを作成
        new_job = BatchJobInfo(
            job_id="batch-new-123",
            input_file="/path/to/questions.txt",
            mode="single",
            step=1,
            min_length=1,
            questions_count=10,
            created_at=datetime.now().isoformat(),
            status="submitted"
        )

        job_manager.save_job(old_job)
        job_manager.save_job(new_job)

        # 30日より古いジョブをクリーンアップ
        deleted_count = job_manager.cleanup_old_jobs(days=30)

        assert deleted_count == 1
        assert job_manager.get_job(old_job.job_id) is None
        assert job_manager.get_job(new_job.job_id) is not None

    def test_batch_job_info_serialization(self):
        """BatchJobInfo シリアライゼーションテスト"""
        job_info = BatchJobInfo(
            job_id="batch-test-123",
            input_file="/path/to/questions.txt",
            mode="single",
            step=1,
            min_length=1,
            questions_count=10,
            created_at=datetime.now().isoformat(),
            status="submitted",
            output_file="results.json"
        )

        # 辞書に変換
        job_dict = job_info.to_dict()

        # 辞書から復元
        restored_job = BatchJobInfo.from_dict(job_dict)

        assert restored_job.job_id == job_info.job_id
        assert restored_job.input_file == job_info.input_file
        assert restored_job.mode == job_info.mode
        assert restored_job.questions_count == job_info.questions_count
        assert restored_job.status == job_info.status
        assert restored_job.output_file == job_info.output_file

    def test_corrupted_jobs_file_handling(self, job_manager, temp_jobs_file):
        """破損したジョブファイルの処理テスト"""
        # 破損したJSONファイルを作成
        with open(temp_jobs_file, 'w') as f:
            f.write('{"invalid": json}')

        # ファイル読み込み時に空の辞書が返されることを確認
        jobs = job_manager.load_jobs()
        assert jobs == {}

    def test_nonexistent_jobs_file_handling(self, job_manager):
        """存在しないジョブファイルの処理テスト"""
        # 存在しないファイルの場合、空の辞書が返されることを確認
        jobs = job_manager.load_jobs()
        assert jobs == {}

    def test_get_job_input_questions(self, job_manager, sample_job_info, tmp_path):
        """ジョブ入力問題取得テスト"""
        # テスト用の問題ファイルを作成
        questions_file = tmp_path / "test_questions.json"
        test_questions = ["問題1", "問題2", "問題3"]

        with open(questions_file, 'w', encoding='utf-8') as f:
            json.dump(test_questions, f, ensure_ascii=False)

        # ジョブ情報の入力ファイルパスを更新
        sample_job_info.input_file = str(questions_file)
        job_manager.save_job(sample_job_info)

        # 問題リストを取得
        questions = job_manager.get_job_input_questions(sample_job_info)

        assert len(questions) == 3
        assert questions[0].original_text == "問題1"
        assert questions[1].original_text == "問題2"
        assert questions[2].original_text == "問題3"