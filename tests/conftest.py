"""
pytest設定とフィクスチャ
"""
import pytest
import os
from unittest.mock import patch


@pytest.fixture
def clean_environment():
    """環境変数をクリアするフィクスチャ"""
    with patch.dict(os.environ, {}, clear=True):
        yield


@pytest.fixture
def mock_api_keys():
    """テスト用APIキーを設定するフィクスチャ"""
    test_env = {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key", 
        "GOOGLE_API_KEY": "test-google-key"
    }
    with patch.dict(os.environ, test_env):
        yield test_env


@pytest.fixture
def sample_messages():
    """テスト用のメッセージ履歴"""
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"}
    ]


@pytest.fixture
def sample_model_config():
    """テスト用のモデル設定"""
    return {
        "GPT-4o": {
            "provider": "openai",
            "model_name": "gpt-4o",
            "api_key_env": "OPENAI_API_KEY",
            "description": "OpenAIの最新マルチモーダルモデル"
        },
        "Claude Sonnet 4": {
            "provider": "anthropic",
            "model_name": "claude-sonnet-4-20250514",
            "api_key_env": "ANTHROPIC_API_KEY",
            "description": "Anthropicの最新Sonnetモデル"
        }
    }