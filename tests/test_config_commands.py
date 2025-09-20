"""設定コマンドのテスト"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from auspiq.commands.config import config as config_command
from auspiq.config import ConfigManager


class TestConfigCommands:
    """設定コマンドのテスト"""

    def setup_method(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"
        self.runner = CliRunner()

    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if self.config_path.exists():
            self.config_path.unlink()
        Path(self.temp_dir).rmdir()

    @patch.dict('os.environ', {}, clear=True)  # 環境変数をクリア
    def test_config_show_default(self):
        """デフォルト設定の表示テスト"""
        result = self.runner.invoke(config_command, ['show', '--config-file', str(self.config_path)])

        assert result.exit_code == 0
        assert "現在の設定" in result.output
        assert "未設定" in result.output  # API Key
        assert "gpt-4" in result.output    # Model
        assert "80" in result.output       # Threshold

    def test_config_show_with_existing_config(self):
        """既存設定の表示テスト"""
        # 設定ファイルを作成
        test_config = {
            "api_key": "sk-test123456",
            "model": "gpt-3.5-turbo",
            "threshold": 85
        }
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        result = self.runner.invoke(config_command, ['show', '--config-file', str(self.config_path)])
        
        assert result.exit_code == 0
        assert "sk-test1..." in result.output  # API Keyの一部表示
        assert "gpt-3.5-turbo" in result.output
        assert "85" in result.output

    def test_config_set_api_key(self):
        """API キー設定テスト"""
        result = self.runner.invoke(config_command, [
            'set', 'api-key', 'sk-test123456789',
            '--config-file', str(self.config_path)
        ])
        
        assert result.exit_code == 0
        assert "設定を更新しました: api-key = sk-test123456789" in result.output
        
        # 設定ファイルが作成され、正しい値が保存されている
        manager = ConfigManager(self.config_path)
        config = manager.get_config()
        assert config.api_key == "sk-test123456789"

    def test_config_set_model(self):
        """モデル設定テスト"""
        result = self.runner.invoke(config_command, [
            'set', 'model', 'gpt-3.5-turbo',
            '--config-file', str(self.config_path)
        ])
        
        assert result.exit_code == 0
        assert "設定を更新しました: model = gpt-3.5-turbo" in result.output

    def test_config_set_threshold(self):
        """閾値設定テスト"""
        result = self.runner.invoke(config_command, [
            'set', 'threshold', '95',
            '--config-file', str(self.config_path)
        ])
        
        assert result.exit_code == 0
        assert "設定を更新しました: threshold = 95" in result.output
        
        manager = ConfigManager(self.config_path)
        config = manager.get_config()
        assert config.threshold == 95

    def test_config_set_invalid_key(self):
        """無効なキーの設定テスト"""
        result = self.runner.invoke(config_command, [
            'set', 'invalid-key', 'value',
            '--config-file', str(self.config_path)
        ])
        
        assert result.exit_code != 0
        assert "無効な設定項目です" in result.output

    def test_config_set_invalid_threshold(self):
        """無効な閾値の設定テスト"""
        result = self.runner.invoke(config_command, [
            'set', 'threshold', '150',
            '--config-file', str(self.config_path)
        ])
        
        assert result.exit_code != 0
        assert "設定値が無効です" in result.output

    def test_config_set_invalid_temperature(self):
        """無効な temperature の設定テスト"""
        result = self.runner.invoke(config_command, [
            'set', 'temperature', '3.0',
            '--config-file', str(self.config_path)
        ])
        
        assert result.exit_code != 0
        assert "temperature は0.0-2.0の範囲で設定してください" in result.output

    def test_config_set_max_tokens(self):
        """最大トークン数設定テスト"""
        result = self.runner.invoke(config_command, [
            'set', 'max-tokens', '1500',
            '--config-file', str(self.config_path)
        ])
        
        assert result.exit_code == 0
        
        manager = ConfigManager(self.config_path)
        config = manager.get_config()
        assert config.max_tokens == 1500

    def test_config_reset(self):
        """設定リセットテスト"""
        # カスタム設定を作成
        manager = ConfigManager(self.config_path)
        manager.update_config(api_key="sk-test", threshold=95)
        
        # リセット（確認なし）
        result = self.runner.invoke(config_command, [
            'reset', '--config-file', str(self.config_path)
        ], input='y\n')
        
        assert result.exit_code == 0
        assert "設定をデフォルト値に戻しました" in result.output
        
        # デフォルト値に戻っている
        manager._config = None  # キャッシュをクリア
        config = manager.get_config()
        assert config.api_key is None
        assert config.threshold == 80

    def test_config_delete(self):
        """設定ファイル削除テスト"""
        # 設定ファイルを作成
        manager = ConfigManager(self.config_path)
        manager.save(manager.get_config())
        assert self.config_path.exists()
        
        # 削除（確認なし）
        result = self.runner.invoke(config_command, [
            'delete', '--config-file', str(self.config_path)
        ], input='y\n')
        
        assert result.exit_code == 0
        assert "設定ファイルを削除しました" in result.output
        assert not self.config_path.exists()

    @patch('auspiq.commands.config.OpenAIClient')
    def test_config_check_valid(self, mock_client_class):
        """設定チェック（正常）テスト"""
        # OpenAIClient のモック設定
        mock_client = mock_client_class.return_value
        mock_client.validate_model.return_value = True

        manager = ConfigManager(self.config_path)
        manager.update_config(api_key="sk-test123456789", model="gpt-4")

        result = self.runner.invoke(config_command, [
            'check', '--config-file', str(self.config_path)
        ])

        assert result.exit_code == 0
        assert "設定に問題はありません" in result.output

    def test_config_check_invalid_api_key(self):
        """設定チェック（無効なAPIキー）テスト"""
        manager = ConfigManager(self.config_path)
        manager.update_config(api_key="invalid-key")
        
        result = self.runner.invoke(config_command, [
            'check', '--config-file', str(self.config_path)
        ])
        
        assert result.exit_code == 0
        assert "設定に問題があります" in result.output
        assert "APIキーの形式が無効です" in result.output

    @patch.dict('os.environ', {}, clear=True)
    def test_config_check_no_api_key(self):
        """設定チェック（APIキーなし）テスト"""
        result = self.runner.invoke(config_command, [
            'check', '--config-file', str(self.config_path)
        ])

        assert result.exit_code == 0
        assert "設定に問題があります" in result.output
        assert "APIキーが設定されていません" in result.output
        assert "APIキーが設定されていないため、モデル名を検証できません" in result.output

    @patch('auspiq.commands.config.OpenAIClient')
    def test_config_check_invalid_model(self, mock_client_class):
        """設定チェック（無効なモデル）テスト"""
        # OpenAIClient のモック設定（モデル検証失敗）
        mock_client = mock_client_class.return_value
        mock_client.validate_model.return_value = False

        manager = ConfigManager(self.config_path)
        manager.update_config(api_key="sk-test123456789", model="invalid-model")

        result = self.runner.invoke(config_command, [
            'check', '--config-file', str(self.config_path)
        ])

        assert result.exit_code == 0
        assert "設定に問題があります" in result.output
        assert "OpenAI APIで利用できないモデルです: invalid-model" in result.output

    @patch('auspiq.commands.config.OpenAIClient')
    def test_config_check_api_error(self, mock_client_class):
        """設定チェック（API例外エラー）テスト"""
        # OpenAIClient のモック設定（例外発生）
        mock_client = mock_client_class.return_value
        mock_client.validate_model.side_effect = Exception("API connection failed")

        manager = ConfigManager(self.config_path)
        manager.update_config(api_key="sk-test123456789", model="gpt-4")

        result = self.runner.invoke(config_command, [
            'check', '--config-file', str(self.config_path)
        ])

        assert result.exit_code == 0
        assert "設定に問題があります" in result.output
        assert "モデル検証でエラーが発生しました: API connection failed" in result.output

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-env123456789'})
    def test_config_show_with_env_key(self):
        """環境変数APIキーありでの表示テスト"""
        result = self.runner.invoke(config_command, [
            'show', '--config-file', str(self.config_path)
        ])
        
        assert result.exit_code == 0
        # 改行を含む場合があるので別々に確認
        assert "環境変数 OPENAI_API_KEY" in result.output
        assert "が利用可能です" in result.output

    def test_key_normalization(self):
        """キー名の正規化テスト（ハイフン → アンダースコア）"""
        result = self.runner.invoke(config_command, [
            'set', 'max-tokens', '1800',
            '--config-file', str(self.config_path)
        ])
        
        assert result.exit_code == 0
        
        manager = ConfigManager(self.config_path)
        config = manager.get_config()
        assert config.max_tokens == 1800