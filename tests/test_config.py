"""設定管理のテスト"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from auspiq.config import Config, ConfigManager


class TestConfig:
    """Config モデルのテスト"""

    def test_default_config(self):
        """デフォルト設定のテスト"""
        config = Config()
        assert config.api_key is None
        assert config.model == "gpt-4"
        assert config.threshold == 80
        assert config.max_tokens == 2000
        assert config.temperature == 0.1

    def test_config_validation(self):
        """設定値の検証テスト"""
        # 正常な値
        config = Config(
            api_key="sk-test123",
            model="gpt-3.5-turbo",
            threshold=90,
            max_tokens=1500,
            temperature=0.5
        )
        assert config.api_key == "sk-test123"
        assert config.model == "gpt-3.5-turbo"
        assert config.threshold == 90
        assert config.max_tokens == 1500
        assert config.temperature == 0.5

    def test_config_extra_forbid(self):
        """不正な設定項目の拒否テスト"""
        with pytest.raises(Exception):  # pydantic.ValidationError
            Config(invalid_field="value")


class TestConfigManager:
    """ConfigManager のテスト"""

    def setup_method(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"

    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if self.config_path.exists():
            self.config_path.unlink()
        
        # ディレクトリ内のファイルをすべて削除
        temp_path = Path(self.temp_dir)
        for file in temp_path.iterdir():
            if file.is_file():
                file.unlink()
            elif file.is_dir():
                for sub_file in file.rglob('*'):
                    if sub_file.is_file():
                        sub_file.unlink()
                for sub_dir in reversed(list(file.rglob('*'))):
                    if sub_dir.is_dir():
                        sub_dir.rmdir()
                file.rmdir()
        temp_path.rmdir()

    def test_load_default_config_when_file_not_exists(self):
        """設定ファイルが存在しない場合のデフォルト設定読み込み"""
        manager = ConfigManager(self.config_path)
        config = manager.load()
        
        assert isinstance(config, Config)
        assert config.api_key is None
        assert config.model == "gpt-4"
        assert config.threshold == 80

    def test_load_config_from_file(self):
        """設定ファイルからの読み込み"""
        test_config = {
            "api_key": "sk-test123",
            "model": "gpt-3.5-turbo",
            "threshold": 85,
            "max_tokens": 1800,
            "temperature": 0.2
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        
        manager = ConfigManager(self.config_path)
        config = manager.load()
        
        assert config.api_key == "sk-test123"
        assert config.model == "gpt-3.5-turbo"
        assert config.threshold == 85
        assert config.max_tokens == 1800
        assert config.temperature == 0.2

    def test_load_invalid_json_file(self):
        """不正なJSONファイルの読み込みエラー"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            f.write("invalid json")
        
        manager = ConfigManager(self.config_path)
        with pytest.raises(ValueError, match="設定ファイルの読み込みに失敗しました"):
            manager.load()

    def test_save_config(self):
        """設定ファイルの保存"""
        config = Config(
            api_key="sk-test456",
            model="gpt-4-turbo",
            threshold=75
        )
        
        manager = ConfigManager(self.config_path)
        manager.save(config)
        
        assert self.config_path.exists()
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data["api_key"] == "sk-test456"
        assert saved_data["model"] == "gpt-4-turbo"
        assert saved_data["threshold"] == 75

    def test_save_without_config(self):
        """設定なしでの保存エラー"""
        manager = ConfigManager(self.config_path)
        with pytest.raises(ValueError, match="保存する設定がありません"):
            manager.save()

    def test_get_config(self):
        """設定取得のテスト"""
        manager = ConfigManager(self.config_path)
        config = manager.get_config()
        assert isinstance(config, Config)

    def test_update_config(self):
        """設定更新のテスト"""
        manager = ConfigManager(self.config_path)
        
        # 初期設定を確認
        initial_config = manager.get_config()
        assert initial_config.api_key is None
        assert initial_config.model == "gpt-4"
        
        # 設定を更新
        updated_config = manager.update_config(
            api_key="sk-newkey",
            model="gpt-3.5-turbo",
            threshold=90
        )
        
        assert updated_config.api_key == "sk-newkey"
        assert updated_config.model == "gpt-3.5-turbo"
        assert updated_config.threshold == 90
        
        # ファイルからの再読み込みで確認
        manager._config = None  # キャッシュをクリア
        reloaded_config = manager.get_config()
        assert reloaded_config.api_key == "sk-newkey"
        assert reloaded_config.model == "gpt-3.5-turbo"
        assert reloaded_config.threshold == 90

    def test_reset_to_default(self):
        """デフォルト設定へのリセット"""
        manager = ConfigManager(self.config_path)
        
        # カスタム設定を保存
        manager.update_config(api_key="sk-test", threshold=95)
        
        # リセット
        reset_config = manager.reset_to_default()
        
        assert reset_config.api_key is None
        assert reset_config.model == "gpt-4"
        assert reset_config.threshold == 80

    def test_delete_config_file(self):
        """設定ファイルの削除"""
        manager = ConfigManager(self.config_path)
        
        # ファイルを作成
        manager.save(Config(api_key="sk-test"))
        assert self.config_path.exists()
        
        # 削除
        manager.delete_config_file()
        assert not self.config_path.exists()

    def test_validate_api_key(self):
        """APIキーの妥当性検証"""
        manager = ConfigManager(self.config_path)
        
        # APIキー未設定
        assert not manager.validate_api_key()
        
        # 空文字のAPIキー
        manager.update_config(api_key="")
        assert not manager.validate_api_key()
        
        # スペースのみのAPIキー
        manager.update_config(api_key="   ")
        assert not manager.validate_api_key()
        
        # 有効なAPIキー
        manager.update_config(api_key="sk-test123")
        assert manager.validate_api_key()

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-env-key'})
    def test_get_api_key_from_env(self):
        """環境変数からのAPIキー取得"""
        manager = ConfigManager(self.config_path)
        assert manager.get_api_key_from_env() == "sk-env-key"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_api_key_from_env_not_set(self):
        """環境変数にAPIキーが設定されていない場合"""
        manager = ConfigManager(self.config_path)
        assert manager.get_api_key_from_env() is None

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-env-key'})
    def test_get_effective_api_key_priority(self):
        """有効なAPIキーの優先順位テスト"""
        manager = ConfigManager(self.config_path)
        
        # 設定ファイルにAPIキーがない場合は環境変数から取得
        assert manager.get_effective_api_key() == "sk-env-key"
        
        # 設定ファイルにAPIキーがある場合はそちらを優先
        manager.update_config(api_key="sk-config-key")
        assert manager.get_effective_api_key() == "sk-config-key"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_effective_api_key_none(self):
        """APIキーが設定されていない場合"""
        manager = ConfigManager(self.config_path)
        assert manager.get_effective_api_key() is None

    def test_config_path_creation(self):
        """設定ファイルディレクトリの自動作成"""
        nested_path = Path(self.temp_dir) / "nested" / "config.json"
        manager = ConfigManager(nested_path)
        
        config = Config(api_key="sk-test")
        manager.save(config)
        
        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_caching_behavior(self):
        """設定のキャッシュ動作"""
        manager = ConfigManager(self.config_path)
        
        # 最初の読み込み
        config1 = manager.load()
        
        # 同じインスタンスが返される
        config2 = manager.load()
        assert config1 is config2
        
        # save後はキャッシュが更新される
        new_config = Config(api_key="sk-new")
        manager.save(new_config)
        config3 = manager.load()
        assert config3 is new_config