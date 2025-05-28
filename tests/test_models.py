"""
models.py のテスト
"""
import pytest
from unittest.mock import patch, MagicMock
import os
from src.models import (
    ModelConfig, 
    create_model, 
    get_available_models, 
    check_model_availability
)


class TestModelConfig:
    """ModelConfigクラスのテスト"""
    
    def test_models_configuration(self):
        """モデル設定が正しく定義されているかテスト"""
        models = ModelConfig.MODELS
        
        # 必要なキーが存在することを確認
        required_keys = ["provider", "model_name", "api_key_env", "description"]
        for model_name, config in models.items():
            for key in required_keys:
                assert key in config, f"モデル '{model_name}' に '{key}' キーがありません"
        
        # 各プロバイダーのモデルが存在することを確認
        providers = [config["provider"] for config in models.values()]
        assert "openai" in providers, "OpenAIモデルが設定されていません"
        assert "anthropic" in providers, "Anthropicモデルが設定されていません" 
        assert "google" in providers, "Googleモデルが設定されていません"


class TestCreateModel:
    """create_model関数のテスト"""
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai-key"})
    @patch('src.models.factory.ChatOpenAI')
    def test_create_openai_model(self, mock_openai):
        """OpenAIモデルの作成テスト"""
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance
        
        result = create_model("GPT-4o")
        
        assert result == mock_instance
        mock_openai.assert_called_once_with(
            model="gpt-4o",
            openai_api_key="test-openai-key",
            temperature=0.7,
            max_tokens=1000
        )
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai-key"})
    @patch('src.models.factory.ChatOpenAI')
    def test_create_openai_gpt41_model(self, mock_openai):
        """OpenAI GPT-4.1モデルの作成テスト"""
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance
        
        result = create_model("GPT-4.1")
        
        assert result == mock_instance
        mock_openai.assert_called_once_with(
            model="gpt-4.1",
            openai_api_key="test-openai-key",
            temperature=0.7,
            max_tokens=1000
        )
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-anthropic-key"})
    @patch('src.models.factory.ChatAnthropic')
    def test_create_anthropic_sonnet_model(self, mock_anthropic):
        """Anthropic Claude Sonnet 4モデルの作成テスト"""
        mock_instance = MagicMock()
        mock_anthropic.return_value = mock_instance
        
        result = create_model("Claude Sonnet 4")
        
        assert result == mock_instance
        mock_anthropic.assert_called_once_with(
            model="claude-sonnet-4-20250514",
            anthropic_api_key="test-anthropic-key",
            temperature=0.7,
            max_tokens=1000
        )
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-anthropic-key"})
    @patch('src.models.factory.ChatAnthropic')
    def test_create_anthropic_opus_model(self, mock_anthropic):
        """Anthropic Claude Opus 4モデルの作成テスト"""
        mock_instance = MagicMock()
        mock_anthropic.return_value = mock_instance
        
        result = create_model("Claude Opus 4")
        
        assert result == mock_instance
        mock_anthropic.assert_called_once_with(
            model="claude-opus-4-20250514",
            anthropic_api_key="test-anthropic-key",
            temperature=0.7,
            max_tokens=1000
        )
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-google-key"})
    @patch('src.models.factory.ChatGoogleGenerativeAI')
    def test_create_google_model(self, mock_google):
        """Googleモデルの作成テスト"""
        mock_instance = MagicMock()
        mock_google.return_value = mock_instance
        
        result = create_model("Gemini 2.5 Flash")
        
        assert result == mock_instance
        mock_google.assert_called_once_with(
            model="gemini-2.5-flash-preview-05-20",
            google_api_key="test-google-key",
            temperature=0.7,
            max_tokens=1000
        )
    
    def test_create_model_invalid_name(self):
        """存在しないモデル名のテスト"""
        result = create_model("InvalidModel")
        assert result is None
    
    @patch.dict(os.environ, {}, clear=True)
    def test_create_model_missing_api_key(self):
        """APIキーが設定されていない場合のテスト"""
        result = create_model("GPT-4o")
        assert result is None
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('src.models.factory.ChatOpenAI')
    def test_create_model_with_custom_params(self, mock_openai):
        """カスタムパラメータでのモデル作成テスト"""
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance
        
        result = create_model("GPT-4o", temperature=0.5, max_tokens=2000)
        
        assert result == mock_instance
        mock_openai.assert_called_once_with(
            model="gpt-4o",
            openai_api_key="test-key",
            temperature=0.5,
            max_tokens=2000
        )
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('src.models.factory.ChatOpenAI')
    def test_create_model_exception_handling(self, mock_openai):
        """モデル作成時の例外処理テスト"""
        mock_openai.side_effect = Exception("API Error")
        
        result = create_model("GPT-4o")
        assert result is None


class TestGetAvailableModels:
    """get_available_models関数のテスト"""
    
    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key"
    })
    def test_get_available_models_with_keys(self):
        """APIキーが設定されている場合のテスト"""
        available = get_available_models()
        
        # OpenAIとAnthropicのモデルが含まれることを確認
        model_names = list(available.keys())
        assert any("GPT" in name for name in model_names), f"GPTモデルが見つかりません: {model_names}"
        assert any("Claude" in name for name in model_names), f"Claudeモデルが見つかりません: {model_names}"
        
        # 設定されたAPIキーに対応するモデルが含まれることを確認
        providers_with_keys = {"openai", "anthropic"}
        actual_providers = {config["provider"] for config in available.values()}
        assert providers_with_keys.issubset(actual_providers), f"期待されるプロバイダー {providers_with_keys} が見つかりません: {actual_providers}"
    
    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "GOOGLE_API_KEY": "test-google-key"
    })
    def test_get_available_models_all_providers(self):
        """全プロバイダーのAPIキーが設定されている場合のテスト"""
        available = get_available_models()
        
        # 全プロバイダーのモデルが含まれることを確認
        model_names = list(available.keys())
        assert any("GPT" in name for name in model_names), f"GPTモデルが見つかりません: {model_names}"
        assert any("Claude" in name for name in model_names), f"Claudeモデルが見つかりません: {model_names}"
        assert any("Gemini" in name for name in model_names), f"Geminiモデルが見つかりません: {model_names}"
        
        # 全プロバイダーが含まれることを確認
        expected_providers = {"openai", "anthropic", "google"}
        actual_providers = {config["provider"] for config in available.values()}
        assert expected_providers == actual_providers, f"期待されるプロバイダー {expected_providers} と実際 {actual_providers} が一致しません"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_available_models_no_keys(self):
        """APIキーが設定されていない場合のテスト"""
        available = get_available_models()
        assert len(available) == 0


class TestCheckModelAvailability:
    """check_model_availability関数のテスト"""
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_check_model_availability_with_key(self):
        """APIキーが設定されている場合のテスト"""
        result = check_model_availability("GPT-4o")
        assert result is True
    
    @patch.dict(os.environ, {}, clear=True)
    def test_check_model_availability_without_key(self):
        """APIキーが設定されていない場合のテスト"""
        result = check_model_availability("GPT-4o")
        assert result is False
    
    def test_check_model_availability_invalid_model(self):
        """存在しないモデルのテスト"""
        result = check_model_availability("InvalidModel")
        assert result is False


class TestIntegration:
    """統合テスト"""
    
    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "GOOGLE_API_KEY": "test-google-key"
    })
    @patch('src.models.factory.ChatOpenAI')
    @patch('src.models.factory.ChatAnthropic')
    @patch('src.models.factory.ChatGoogleGenerativeAI')
    def test_end_to_end_workflow(self, mock_google, mock_anthropic, mock_openai):
        """エンドツーエンドのワークフローテスト"""
        # モックの設定
        mock_openai.return_value = MagicMock()
        mock_anthropic.return_value = MagicMock()
        mock_google.return_value = MagicMock()
        
        # 利用可能なモデルを取得
        available = get_available_models()
        assert len(available) > 0
        
        # 各モデルの作成をテスト
        for model_name in available.keys():
            model = create_model(model_name)
            assert model is not None
            
            # 可用性チェック
            assert check_model_availability(model_name) is True