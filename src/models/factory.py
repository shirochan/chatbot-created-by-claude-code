"""
AIモデルのファクトリー関数
"""
import os
import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel

from .config import ModelConfig, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS

# ロガーの設定
logger = logging.getLogger(__name__)

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
        "temperature": kwargs.get("temperature", DEFAULT_TEMPERATURE),
        "max_tokens": kwargs.get("max_tokens", DEFAULT_MAX_TOKENS)
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
        else:
            logger.error(f"未対応のプロバイダー: {config['provider']} (モデル: {model_name})")
            return None
    except Exception as e:
        logger.error(f"モデル作成エラー: {e}")
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