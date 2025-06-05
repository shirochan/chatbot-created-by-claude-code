"""
設定管理ユーティリティ
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any

def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    設定ファイルを読み込み
    
    Args:
        config_path: 設定ファイルのパス
        
    Returns:
        Dict: 設定辞書
    """
    if config_path is None:
        # プロジェクトルートのconfig.yamlを探す
        current_dir = Path(__file__).parent.parent.parent
        config_path = current_dir / "config.yaml"
    
    if not os.path.exists(config_path):
        # デフォルト設定を返す
        return {
            "app": {
                "title": "AIチャットボット",
                "page_icon": "🤖",
                "layout": "wide"
            },
            "logging": {
                "level": "INFO"
            },
            "chat": {
                "max_history": 100,
                "default_model": "GPT-4o"
            }
        }
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_app_config() -> Dict[str, Any]:
    """アプリケーション設定を取得"""
    config = load_config()
    return config.get("app", {})

def get_logging_config() -> Dict[str, Any]:
    """ログ設定を取得"""
    config = load_config()
    return config.get("logging", {})

def get_chat_config() -> Dict[str, Any]:
    """チャット設定を取得"""
    config = load_config()
    return config.get("chat", {})

def get_file_upload_config() -> Dict[str, Any]:
    """ファイルアップロード設定を取得"""
    config = load_config()
    return config.get("file_upload", {})

def get_history_config() -> Dict[str, Any]:
    """履歴管理設定を取得"""
    config = load_config()
    return config.get("history", {})