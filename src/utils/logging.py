"""
ログ設定管理ユーティリティ
"""
import logging
import sys
from typing import Optional

def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    logger_name: Optional[str] = None
) -> logging.Logger:
    """
    ログ設定をセットアップ
    
    Args:
        level: ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: ログフォーマット文字列
        logger_name: ロガー名
        
    Returns:
        logging.Logger: 設定されたロガー
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ルートロガーの設定
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 指定されたロガーを取得
    logger = logging.getLogger(logger_name)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    指定された名前のロガーを取得
    
    Args:
        name: ロガー名
        
    Returns:
        logging.Logger: ロガーインスタンス
    """
    return logging.getLogger(name)