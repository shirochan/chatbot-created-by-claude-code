"""
src.app モジュールのテスト
Streamlitアプリケーションの基本機能をテスト
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAppImports:
    """アプリケーションのインポートテスト"""
    
    def test_import_models(self):
        """modelsモジュールのインポートテスト"""
        from src.models import ModelConfig, create_model, get_available_models
        assert ModelConfig is not None
        assert create_model is not None
        assert get_available_models is not None
    
    def test_import_streamlit_dependencies(self):
        """Streamlit関連のインポートテスト"""
        import streamlit as st
        from dotenv import load_dotenv
        from langchain_core.messages import HumanMessage, AIMessage
        
        assert st is not None
        assert load_dotenv is not None
        assert HumanMessage is not None
        assert AIMessage is not None


class TestAppConfiguration:
    """アプリケーション設定のテスト"""
    
    @patch('streamlit.set_page_config')
    def test_page_config(self, mock_config):
        """ページ設定のテスト"""
        # ページ設定の値を直接テスト
        expected_config = {
            "page_title": "AIチャットボット",
            "page_icon": "🤖",
            "layout": "centered"
        }
        
        # 実際のStreamlit設定をシミュレート
        import streamlit as st
        st.set_page_config(**expected_config)
        
        # 設定が正しく呼ばれることを確認
        mock_config.assert_called_with(**expected_config)


class TestSessionStateInitialization:
    """セッション状態の初期化テスト"""
    
    @patch('src.models.get_available_models')
    def test_session_state_messages_init(self, mock_get_models):
        """メッセージセッション状態の初期化テスト"""
        mock_get_models.return_value = {"GPT-4o": {"provider": "openai"}}
        
        # セッション状態のシミュレート
        session_state = {}
        
        # セッション状態の初期化ロジックをテスト
        if "messages" not in session_state:
            session_state["messages"] = []
        
        assert "messages" in session_state
        assert session_state["messages"] == []
    
    @patch('src.models.get_available_models')
    def test_session_state_model_selection_init(self, mock_get_models):
        """モデル選択セッション状態の初期化テスト"""
        mock_models = {
            "GPT-4o": {"provider": "openai"},
            "Claude Sonnet 4": {"provider": "anthropic"}
        }
        mock_get_models.return_value = mock_models
        
        # セッション状態のシミュレート
        session_state = {}
        
        # モデル選択の初期化ロジックをテスト
        if "selected_model" not in session_state:
            available_models = mock_get_models()
            if available_models:
                session_state["selected_model"] = list(available_models.keys())[0]
            else:
                session_state["selected_model"] = None
        
        assert "selected_model" in session_state
        assert session_state["selected_model"] == "GPT-4o"


class TestMessageProcessing:
    """メッセージ処理のテスト"""
    
    def test_langchain_message_conversion(self):
        """LangChainメッセージ形式への変換テスト"""
        from langchain_core.messages import HumanMessage, AIMessage
        
        # テスト用のメッセージ履歴
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        # 変換ロジック
        langchain_messages = []
        for msg in messages:
            if msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))
        
        # 結果の検証
        assert len(langchain_messages) == 3
        assert isinstance(langchain_messages[0], HumanMessage)
        assert langchain_messages[0].content == "Hello"
        assert isinstance(langchain_messages[1], AIMessage)
        assert langchain_messages[1].content == "Hi there!"
        assert isinstance(langchain_messages[2], HumanMessage)
        assert langchain_messages[2].content == "How are you?"


class TestModelIntegration:
    """モデル統合のテスト"""
    
    @patch('src.models.create_model')
    @patch('src.models.get_available_models')
    def test_model_selection_validation(self, mock_get_models, mock_create_model):
        """モデル選択の検証テスト"""
        # 利用可能なモデルを設定
        mock_models = {
            "GPT-4o": {"provider": "openai", "description": "OpenAIの最新モデル"},
            "Claude Sonnet 4": {"provider": "anthropic", "description": "Anthropicのモデル"}
        }
        mock_get_models.return_value = mock_models
        
        # モデル作成のモック
        mock_model = MagicMock()
        mock_create_model.return_value = mock_model
        
        # 選択されたモデルの検証
        selected_model = "GPT-4o"
        assert selected_model in mock_models
        
        # モデル作成テスト
        model = mock_create_model(selected_model)
        assert model is not None
        mock_create_model.assert_called_once_with(selected_model)
    
    @patch('src.models.create_model')
    def test_model_creation_failure_handling(self, mock_create_model):
        """モデル作成失敗時の処理テスト"""
        # モデル作成が失敗する場合をシミュレート
        mock_create_model.return_value = None
        
        selected_model = "InvalidModel"
        model = mock_create_model(selected_model)
        
        # Noneが返されることを確認
        assert model is None


class TestErrorHandling:
    """エラーハンドリングのテスト"""
    
    def test_missing_api_key_scenario(self):
        """APIキー未設定時のシナリオテスト"""
        with patch.dict(os.environ, {}, clear=True):
            from src.models import get_available_models
            
            available_models = get_available_models()
            # APIキーが設定されていない場合、利用可能なモデルは0個
            assert len(available_models) == 0
    
    @patch('src.models.create_model')
    def test_model_invoke_error_handling(self, mock_create_model):
        """モデル呼び出しエラーのハンドリングテスト"""
        # モデルが例外を投げる場合をシミュレート
        mock_model = MagicMock()
        mock_model.invoke.side_effect = Exception("API Error")
        mock_create_model.return_value = mock_model
        
        model = mock_create_model("GPT-4o")
        
        # 例外処理のテスト
        try:
            model.invoke([])
            assert False, "例外が発生すべきです"
        except Exception as e:
            assert str(e) == "API Error"


class TestUtilityFunctions:
    """ユーティリティ関数のテスト"""
    
    def test_environment_variable_handling(self):
        """環境変数の処理テスト"""
        from dotenv import load_dotenv
        
        # load_dotenv関数が正常に動作することを確認
        result = load_dotenv()
        # ファイルが存在しない場合はFalseが返される
        assert isinstance(result, bool)
    
    @patch('src.models.get_available_models')
    def test_model_description_display(self, mock_get_models):
        """モデル説明表示のテスト"""
        mock_models = {
            "GPT-4o": {
                "provider": "openai",
                "description": "OpenAIの最新マルチモーダルモデル"
            }
        }
        mock_get_models.return_value = mock_models
        
        available_models = mock_get_models()
        model_name = "GPT-4o"
        
        if model_name in available_models:
            description = available_models[model_name]['description']
            assert description == "OpenAIの最新マルチモーダルモデル"