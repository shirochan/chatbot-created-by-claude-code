"""
AIモデルの設定と管理を行うモジュール
"""
import os
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel

class ModelConfig:
    """AIモデルの設定クラス"""
    
    # 利用可能なモデル設定
    MODELS = {
        "GPT-4o": {
            "provider": "openai",
            "model_name": "gpt-4o",
            "api_key_env": "OPENAI_API_KEY",
            "description": "OpenAIの最新マルチモーダルモデル"
        },
        "GPT-4.1": {
            "provider": "openai", 
            "model_name": "gpt-4.1",
            "api_key_env": "OPENAI_API_KEY",
            "description": "最新のGPTモデル、コーディングと推論が大幅向上"
        },
        "Claude Sonnet 4": {
            "provider": "anthropic",
            "model_name": "claude-sonnet-4-20250514",
            "api_key_env": "ANTHROPIC_API_KEY", 
            "description": "スマートで効率的な日常使いに最適なモデル"
        },
        "Claude Opus 4": {
            "provider": "anthropic",
            "model_name": "claude-opus-4-20250514",
            "api_key_env": "ANTHROPIC_API_KEY",
            "description": "世界最高のコーディングモデル、最も知的なAI"
        },
        "Gemini 2.5 Flash": {
            "provider": "google", 
            "model_name": "gemini-2.5-flash-preview-05-20",
            "api_key_env": "GOOGLE_API_KEY",
            "description": "思考機能付きハイブリッド推論モデル、速度と効率重視"
        }
    }

def create_model(model_name: str, **kwargs) -> Optional[BaseChatModel]:
    """
    指定されたモデル名に基づいてLangChainモデルインスタンスを作成
    
    Args:
        model_name: モデル名（ModelConfig.MODELSのキー）
        **kwargs: モデルに渡す追加パラメータ
        
    Returns:
        BaseChatModel: 作成されたモデルインスタンス、または None（エラー時）
    """
    if model_name not in ModelConfig.MODELS:
        return None
        
    config = ModelConfig.MODELS[model_name]
    api_key = os.getenv(config["api_key_env"])
    
    if not api_key:
        return None
    
    # デフォルトパラメータ
    default_params = {
        "temperature": kwargs.get("temperature", 0.7),
        "max_tokens": kwargs.get("max_tokens", 1000)
    }
    
    try:
        if config["provider"] == "openai":
            return ChatOpenAI(
                model=config["model_name"],
                openai_api_key=api_key,
                **default_params
            )
        elif config["provider"] == "anthropic":
            return ChatAnthropic(
                model=config["model_name"],
                anthropic_api_key=api_key,
                **default_params
            )
        elif config["provider"] == "google":
            return ChatGoogleGenerativeAI(
                model=config["model_name"],
                google_api_key=api_key,
                **default_params
            )
    except Exception as e:
        print(f"モデル作成エラー: {e}")
        return None
    
    return None

def get_available_models() -> Dict[str, Dict[str, Any]]:
    """
    利用可能なモデルの一覧を取得（APIキーが設定されているもののみ）
    
    Returns:
        Dict: 利用可能なモデルの辞書
    """
    available = {}
    for model_name, config in ModelConfig.MODELS.items():
        api_key = os.getenv(config["api_key_env"])
        if api_key:
            available[model_name] = config
    return available

def check_model_availability(model_name: str) -> bool:
    """
    指定されたモデルが利用可能かチェック
    
    Args:
        model_name: チェックするモデル名
        
    Returns:
        bool: 利用可能な場合True
    """
    if model_name not in ModelConfig.MODELS:
        return False
    
    config = ModelConfig.MODELS[model_name]
    api_key = os.getenv(config["api_key_env"])
    return bool(api_key)