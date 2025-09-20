"""バッチジョブ管理モジュール"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

from .logging_config import get_logger
from .models import QuizQuestion

logger = get_logger(__name__)


@dataclass
class BatchJobInfo:
    """バッチジョブ情報"""
    job_id: str
    input_file: str
    mode: str
    step: int
    min_length: int
    questions_count: int
    created_at: str
    status: str = "submitted"
    completed_at: Optional[str] = None
    output_file: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'BatchJobInfo':
        """辞書から作成"""
        return cls(**data)


class BatchJobManager:
    """バッチジョブの追跡・管理を行うクラス"""

    def __init__(self, jobs_file: Optional[Path] = None):
        if jobs_file is None:
            self.jobs_file = Path.home() / ".auspiq-jobs.json"
        else:
            self.jobs_file = jobs_file

    def save_job(self, job_info: BatchJobInfo) -> None:
        """ジョブ情報を保存"""
        jobs = self.load_jobs()
        jobs[job_info.job_id] = job_info.to_dict()

        try:
            # ディレクトリが存在しない場合は作成
            self.jobs_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.jobs_file, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved job {job_info.job_id} to {self.jobs_file}")

        except Exception as e:
            logger.error(f"Failed to save job {job_info.job_id}: {e}")
            raise

    def load_jobs(self) -> Dict[str, dict]:
        """保存されたジョブ一覧を読み込み"""
        if not self.jobs_file.exists():
            return {}

        try:
            with open(self.jobs_file, 'r', encoding='utf-8') as f:
                jobs = json.load(f)
            return jobs
        except Exception as e:
            logger.warning(f"Failed to load jobs file {self.jobs_file}: {e}")
            return {}

    def get_job(self, job_id: str) -> Optional[BatchJobInfo]:
        """特定のジョブ情報を取得"""
        jobs = self.load_jobs()
        job_data = jobs.get(job_id)
        if job_data:
            return BatchJobInfo.from_dict(job_data)
        return None

    def update_job_status(self, job_id: str, status: str, **kwargs) -> None:
        """ジョブステータスを更新"""
        jobs = self.load_jobs()
        if job_id not in jobs:
            logger.warning(f"Job {job_id} not found in local records")
            return

        job_data = jobs[job_id]
        job_data['status'] = status

        # 追加情報を更新
        for key, value in kwargs.items():
            if key in job_data:
                job_data[key] = value

        if status == "completed":
            job_data['completed_at'] = datetime.now().isoformat()

        jobs[job_id] = job_data

        try:
            with open(self.jobs_file, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            logger.info(f"Updated job {job_id} status to {status}")
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {e}")

    def list_jobs(self, limit: Optional[int] = None) -> List[BatchJobInfo]:
        """ジョブ一覧を取得（作成日時の降順）"""
        jobs = self.load_jobs()

        job_infos = []
        for job_data in jobs.values():
            try:
                job_info = BatchJobInfo.from_dict(job_data)
                job_infos.append(job_info)
            except Exception as e:
                logger.warning(f"Failed to parse job data: {e}")
                continue

        # 作成日時で降順ソート
        job_infos.sort(key=lambda x: x.created_at, reverse=True)

        if limit:
            job_infos = job_infos[:limit]

        return job_infos

    def delete_job(self, job_id: str) -> bool:
        """ジョブ記録を削除"""
        jobs = self.load_jobs()
        if job_id not in jobs:
            return False

        del jobs[job_id]

        try:
            with open(self.jobs_file, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            logger.info(f"Deleted job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            return False

    def cleanup_old_jobs(self, days: int = 30) -> int:
        """古いジョブ記録をクリーンアップ"""
        jobs = self.load_jobs()
        current_time = datetime.now()
        deleted_count = 0

        jobs_to_delete = []
        for job_id, job_data in jobs.items():
            try:
                created_at = datetime.fromisoformat(job_data['created_at'])
                age_days = (current_time - created_at).days

                if age_days > days:
                    jobs_to_delete.append(job_id)
                    deleted_count += 1

            except Exception as e:
                logger.warning(f"Failed to parse job {job_id} created_at: {e}")

        # 削除実行
        for job_id in jobs_to_delete:
            del jobs[job_id]

        if deleted_count > 0:
            try:
                with open(self.jobs_file, 'w', encoding='utf-8') as f:
                    json.dump(jobs, f, indent=2, ensure_ascii=False)
                logger.info(f"Cleaned up {deleted_count} old jobs")
            except Exception as e:
                logger.error(f"Failed to cleanup old jobs: {e}")

        return deleted_count

    def get_job_input_questions(self, job_info: BatchJobInfo) -> List[QuizQuestion]:
        """ジョブの入力問題リストを復元"""
        from .file_io import QuestionLoader

        try:
            questions = QuestionLoader.load_questions(job_info.input_file)
            logger.info(f"Loaded {len(questions)} questions from {job_info.input_file}")
            return questions
        except Exception as e:
            logger.error(f"Failed to load questions from {job_info.input_file}: {e}")
            raise