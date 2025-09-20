"""プロンプトテンプレートのテスト"""
import pytest
from unittest.mock import patch, mock_open

from auspiq.prompts import PromptTemplate


class TestPromptTemplate:
    """PromptTemplate クラスのテスト"""
    
    def test_get_system_prompt(self):
        """システムプロンプトの取得が正常に動作することを確認"""
        system_prompt = PromptTemplate.get_system_prompt()
        
        # 重要なキーワードが含まれていることを確認
        assert "競技クイズ" in system_prompt
        assert "SC型" in system_prompt
        assert "OV型" in system_prompt
        assert "60文字〜100文字" in system_prompt
        assert "知名度の低い情報が前置され" in system_prompt
        
        # 空でないことを確認
        assert len(system_prompt.strip()) > 100
    
    def test_get_user_prompt_template(self):
        """ユーザープロンプトテンプレートの取得が正常に動作することを確認"""
        user_template = PromptTemplate.get_user_prompt_template()
        
        # テンプレート変数が含まれていることを確認
        assert "{max_candidates}" in user_template
        assert "{text_so_far}" in user_template
        
        # JSON形式の指定が含まれていることを確認
        assert "JSON形式" in user_template
        assert '"candidates"' in user_template
        assert '"total_probability"' in user_template
        
        # 空でないことを確認
        assert len(user_template.strip()) > 100
    
    def test_user_prompt_template_formatting(self):
        """ユーザープロンプトテンプレートが正しくフォーマットされることを確認"""
        text_so_far = "静岡県と山梨県の県境に位置する、標高／"
        max_candidates = 3
        
        user_template = PromptTemplate.get_user_prompt_template()
        user_prompt = user_template.format(
            text_so_far=text_so_far,
            max_candidates=max_candidates
        )
        
        # フォーマットされた値が含まれていることを確認
        assert text_so_far in user_prompt
        assert str(max_candidates) in user_prompt
        
        # JSON形式の指定が含まれていることを確認
        assert "JSON形式" in user_prompt
        assert "candidates" in user_prompt
        assert "total_probability" in user_prompt
        assert "text_so_far" in user_prompt
    
    def test_get_prediction_messages_structure(self):
        """get_prediction_messages の戻り値構造が正しいことを確認"""
        text_so_far = "静岡県と山梨県の県境に位置する、標高／"
        max_candidates = 5
        
        messages = PromptTemplate.get_prediction_messages(text_so_far, max_candidates)
        
        # リストであることを確認
        assert isinstance(messages, list)
        assert len(messages) == 2
        
        # システムメッセージの確認
        system_message = messages[0]
        assert system_message["role"] == "system"
        assert "content" in system_message
        assert len(system_message["content"]) > 0
        
        # ユーザーメッセージの確認
        user_message = messages[1]
        assert user_message["role"] == "user"
        assert "content" in user_message
        assert text_so_far in user_message["content"]
        assert str(max_candidates) in user_message["content"]
    
    def test_get_prediction_messages_default_candidates(self):
        """get_prediction_messages でデフォルトの候補数が正しく処理されることを確認"""
        text_so_far = "テスト／"
        
        messages = PromptTemplate.get_prediction_messages(text_so_far)
        
        user_content = messages[1]["content"]
        assert "5つまで" in user_content  # デフォルトは5
    
    def test_get_prediction_messages_custom_candidates(self):
        """get_prediction_messages でカスタム候補数が正しく処理されることを確認"""
        text_so_far = "テスト／"
        max_candidates = 3
        
        messages = PromptTemplate.get_prediction_messages(text_so_far, max_candidates)
        
        user_content = messages[1]["content"]
        assert f"{max_candidates}つまで" in user_content
        assert f"{max_candidates}つの候補" in user_content
    
    def test_prompt_contains_json_schema(self):
        """プロンプトに期待されるJSONスキーマが含まれていることを確認"""
        messages = PromptTemplate.get_prediction_messages("test／", 5)
        user_content = messages[1]["content"]
        
        # JSON スキーマの要素が含まれていることを確認
        assert '"candidates"' in user_content
        assert '"full_text"' in user_content
        assert '"answer"' in user_content
        assert '"probability"' in user_content
        assert '"total_probability"' in user_content
    
    def test_prompt_contains_probability_instructions(self):
        """プロンプトに蓋然性に関する指示が含まれていることを確認"""
        messages = PromptTemplate.get_prediction_messages("test／", 5)
        user_content = messages[1]["content"]
        
        # 蓋然性に関する重要な指示が含まれていることを確認
        assert "0〜100%" in user_content
        assert "全体が100%" in user_content
        assert "合計値" in user_content
        assert "<1%" in user_content
    
    def test_special_characters_in_text_so_far(self):
        """text_so_far に特殊文字が含まれても正しく処理されることを確認"""
        special_text = "特殊文字「」『』（）／"
        
        messages = PromptTemplate.get_prediction_messages(special_text, 3)
        user_content = messages[1]["content"]
        
        # 特殊文字がそのまま含まれていることを確認
        assert special_text in user_content
    
    def test_long_text_so_far(self):
        """長いテキストでも正しく処理されることを確認"""
        long_text = "これは非常に長いテキストです。" * 10 + "／"
        
        messages = PromptTemplate.get_prediction_messages(long_text, 5)
        user_content = messages[1]["content"]
        
        # 長いテキストが含まれていることを確認
        assert long_text in user_content
        
        # メッセージ構造は変わらないことを確認
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
    
    def test_cache_mechanism(self):
        """キャッシュ機能が正常に動作することを確認"""
        # 最初の呼び出し
        system_prompt1 = PromptTemplate.get_system_prompt()
        user_template1 = PromptTemplate.get_user_prompt_template()
        
        # 二回目の呼び出し（キャッシュから取得される）
        system_prompt2 = PromptTemplate.get_system_prompt()
        user_template2 = PromptTemplate.get_user_prompt_template()
        
        # 同じ内容であることを確認
        assert system_prompt1 == system_prompt2
        assert user_template1 == user_template2
    
    def test_reload_prompts(self):
        """プロンプト再読み込み機能が正常に動作することを確認"""
        # 初回読み込み
        PromptTemplate.get_system_prompt()
        PromptTemplate.get_user_prompt_template()
        
        # キャッシュが設定されていることを確認
        assert PromptTemplate._system_prompt_cache is not None
        assert PromptTemplate._user_prompt_template_cache is not None
        
        # キャッシュクリア
        PromptTemplate.reload_prompts()
        
        # キャッシュがクリアされていることを確認
        assert PromptTemplate._system_prompt_cache is None
        assert PromptTemplate._user_prompt_template_cache is None
    
    def test_validate_prompt_files(self):
        """プロンプトファイル検証機能が正常に動作することを確認"""
        result = PromptTemplate.validate_prompt_files()
        assert result is True
    
    @patch('builtins.open', side_effect=FileNotFoundError())
    def test_file_not_found_error(self, mock_open):
        """ファイルが見つからない場合の処理を確認"""
        # キャッシュをクリア
        PromptTemplate.reload_prompts()
        
        with pytest.raises(FileNotFoundError):
            PromptTemplate.get_system_prompt()
    
    @patch('builtins.open', mock_open(read_data="テストプロンプト"))
    def test_file_reading(self):
        """ファイル読み込み機能が正常に動作することを確認"""
        # キャッシュをクリア
        PromptTemplate.reload_prompts()
        
        prompt = PromptTemplate.get_system_prompt()
        assert prompt == "テストプロンプト"
