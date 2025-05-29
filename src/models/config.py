"""
AIモデルの設定クラス
"""

# デフォルト値の定数
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1000

class ModelConfig:
    """AIモデルの設定クラス"""
    
    # 利用可能なモデル設定
    MODELS = {
        "GPT-4o": {
            "provider": "openai",
            "model_name": "gpt-4o",
            "api_key_env": "OPENAI_API_KEY",
            "description": "OpenAIの最新マルチモーダルモデル",
            "supports_vision": True
        },
        "GPT-4.1": {
            "provider": "openai", 
            "model_name": "gpt-4.1",
            "api_key_env": "OPENAI_API_KEY",
            "description": "最新のGPTモデル、コーディングと推論が大幅向上",
            "supports_vision": False
        },
        "Claude Sonnet 4": {
            "provider": "anthropic",
            "model_name": "claude-sonnet-4-20250514",
            "api_key_env": "ANTHROPIC_API_KEY", 
            "description": "スマートで効率的な日常使いに最適なモデル",
            "supports_vision": True
        },
        "Claude Opus 4": {
            "provider": "anthropic",
            "model_name": "claude-opus-4-20250514",
            "api_key_env": "ANTHROPIC_API_KEY",
            "description": "世界最高のコーディングモデル、最も知的なAI",
            "supports_vision": True
        },
        "Gemini 2.5 Flash": {
            "provider": "google", 
            "model_name": "gemini-2.5-flash-preview-05-20",
            "api_key_env": "GOOGLE_API_KEY",
            "description": "思考機能付きハイブリッド推論モデル、速度と効率重視",
            "supports_vision": True
        }
    }