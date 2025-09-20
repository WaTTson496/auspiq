"""プロンプトテンプレートの管理"""
from typing import Dict, Any, Optional
from pathlib import Path

from .logging_config import get_logger

logger = get_logger(__name__)


class PromptTemplate:
    """プロンプトテンプレート管理クラス"""
    
    # プロンプトファイルのパス
    _PROMPTS_DIR = Path(__file__).parent / "prompts"
    _SYSTEM_PROMPT_FILE = _PROMPTS_DIR / "system_prompt.md"
    _USER_PROMPT_TEMPLATE_FILE = _PROMPTS_DIR / "user_prompt_template.md"
    
    # キャッシュ用
    _system_prompt_cache: Optional[str] = None
    _user_prompt_template_cache: Optional[str] = None
    
    @classmethod
    def _load_prompt_file(cls, file_path: Path) -> str:
        """プロンプトファイルを読み込む"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.error(f"プロンプトファイルが見つかりません: {file_path}")
            raise
        except Exception as e:
            logger.error(f"プロンプトファイル読み込みエラー: {file_path}, {e}")
            raise
    
    @classmethod
    def get_system_prompt(cls) -> str:
        """システムプロンプトを取得する"""
        if cls._system_prompt_cache is None:
            cls._system_prompt_cache = cls._load_prompt_file(cls._SYSTEM_PROMPT_FILE)
        return cls._system_prompt_cache
    
    @classmethod
    def get_user_prompt_template(cls) -> str:
        """ユーザープロンプトテンプレートを取得する"""
        if cls._user_prompt_template_cache is None:
            cls._user_prompt_template_cache = cls._load_prompt_file(cls._USER_PROMPT_TEMPLATE_FILE)
        return cls._user_prompt_template_cache
    
    @classmethod
    def get_prediction_messages(cls, text_so_far: str, max_candidates: int = 5) -> list[Dict[str, Any]]:
        """予測用のメッセージリストを生成する"""
        logger.debug(f"Generating prediction messages for text: '{text_so_far}', max_candidates: {max_candidates}")

        logger.debug("Loading system prompt...")
        system_prompt = cls.get_system_prompt()
        logger.debug(f"System prompt loaded: {len(system_prompt)} characters")

        logger.debug("Loading user prompt template...")
        user_prompt_template = cls.get_user_prompt_template()
        logger.debug(f"User prompt template loaded: {len(user_prompt_template)} characters")

        logger.debug("Formatting user prompt with parameters...")
        user_prompt = user_prompt_template.format(
            text_so_far=text_so_far,
            max_candidates=max_candidates
        )
        logger.debug(f"Formatted user prompt: {len(user_prompt)} characters")

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        logger.debug(f"Generated {len(messages)} messages for API call")
        logger.debug(f"Total message content length: {sum(len(msg['content']) for msg in messages)} characters")

        return messages
    
    @classmethod
    def reload_prompts(cls) -> None:
        """プロンプトキャッシュをクリアして再読み込みを強制する"""
        cls._system_prompt_cache = None
        cls._user_prompt_template_cache = None
        logger.info("プロンプトキャッシュをクリアしました")
    
    @classmethod
    def validate_prompt_files(cls) -> bool:
        """プロンプトファイルの存在と読み込み可能性を確認する"""
        try:
            cls._load_prompt_file(cls._SYSTEM_PROMPT_FILE)
            cls._load_prompt_file(cls._USER_PROMPT_TEMPLATE_FILE)
            return True
        except Exception as e:
            logger.error(f"プロンプトファイル検証エラー: {e}")
            return False
