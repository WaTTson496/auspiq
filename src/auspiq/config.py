"""設定管理モジュール"""
import json
import os
from pathlib import Path
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class Config(BaseModel):
    """アプリケーション設定を管理するクラス"""

    model_config = ConfigDict(extra="forbid")

    api_key: Optional[str] = Field(None, description="OpenAI API key")
    model: str = Field("gpt-4", description="OpenAI model name")
    threshold: int = Field(80, description="Probability threshold for auto-pause")
    max_tokens: int = Field(2000, description="Maximum tokens for API requests")
    temperature: float = Field(0.1, description="Temperature for API requests")
    console_log_level: str = Field("INFO", description="Console log level (DEBUG, INFO, WARNING, ERROR)")
    file_log_level: str = Field("DEBUG", description="File log level (DEBUG, INFO, WARNING, ERROR)")


class ConfigManager:
    """設定ファイルの読み書きを管理するクラス"""
    
    DEFAULT_CONFIG_PATH = Path.home() / ".auspiq.json"
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        if config_path is None:
            self.config_path = self.DEFAULT_CONFIG_PATH
        elif isinstance(config_path, str):
            self.config_path = Path(config_path)
        else:
            self.config_path = config_path
        self._config: Optional[Config] = None
    
    def load(self) -> Config:
        """設定ファイルを読み込む"""
        if self._config is not None:
            return self._config
            
        if not self.config_path.exists():
            self._config = Config()
            return self._config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._config = Config(**data)
        except (json.JSONDecodeError, Exception) as e:
            raise ValueError(f"設定ファイルの読み込みに失敗しました: {e}")
        
        return self._config
    
    def save(self, config: Optional[Config] = None) -> None:
        """設定ファイルに保存する"""
        if config is not None:
            self._config = config
        
        if self._config is None:
            raise ValueError("保存する設定がありません")
        
        # ディレクトリが存在しない場合は作成
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config.model_dump(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ValueError(f"設定ファイルの保存に失敗しました: {e}")
    
    def get_config(self) -> Config:
        """現在の設定を取得する"""
        return self.load()
    
    def update_config(self, **kwargs) -> Config:
        """設定を更新する"""
        current_config = self.load()
        updated_data = current_config.model_dump()
        updated_data.update(kwargs)
        
        new_config = Config(**updated_data)
        self.save(new_config)
        return new_config
    
    def reset_to_default(self) -> Config:
        """設定をデフォルトに戻す"""
        self._config = Config()
        self.save()
        return self._config
    
    def delete_config_file(self) -> None:
        """設定ファイルを削除する"""
        if self.config_path.exists():
            self.config_path.unlink()
        self._config = None
    
    def validate_api_key(self) -> bool:
        """API キーが設定されているかチェックする"""
        config = self.load()
        return config.api_key is not None and config.api_key.strip() != ""
    
    def get_api_key_from_env(self) -> Optional[str]:
        """環境変数からAPIキーを取得する"""
        return os.getenv("OPENAI_API_KEY")
    
    def get_effective_api_key(self) -> Optional[str]:
        """有効なAPIキーを取得する（設定ファイル優先、次に環境変数）"""
        config = self.load()
        if config.api_key and config.api_key.strip():
            return config.api_key
        return self.get_api_key_from_env()