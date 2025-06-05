"""
チャット履歴管理のための高レベルAPIモジュール
Streamlitアプリケーションとデータベースの橋渡しを行う
"""

import uuid
from typing import List, Dict, Any, Optional
from PIL import Image
import logging

from .database import ChatHistoryDatabase

logger = logging.getLogger(__name__)

class ChatHistoryManager:
    """チャット履歴管理クラス"""
    
    def __init__(self, db_path: str = "chat_history.db"):
        """
        履歴管理マネージャーを初期化
        
        Args:
            db_path: データベースファイルのパス
        """
        self.db = ChatHistoryDatabase(db_path)
        self._current_session_id = None
    
    def start_new_session(self, model_name: str = None) -> str:
        """
        新しいチャットセッションを開始
        
        Args:
            model_name: 使用するモデル名
            
        Returns:
            新しいセッションID
        """
        session_id = str(uuid.uuid4())
        self._current_session_id = session_id
        logger.info(f"新しいセッション開始: {session_id}, model: {model_name}")
        return session_id
    
    def set_current_session(self, session_id: str):
        """
        現在のセッションを設定
        
        Args:
            session_id: セッションID
        """
        self._current_session_id = session_id
        logger.debug(f"現在のセッション設定: {session_id}")
    
    def get_current_session_id(self) -> Optional[str]:
        """
        現在のセッションIDを取得
        
        Returns:
            現在のセッションID（設定されていない場合はNone）
        """
        return self._current_session_id
    
    def save_user_message(self, content: str, image: Optional[Image.Image] = None, 
                         model_name: str = None) -> int:
        """
        ユーザーメッセージを保存
        
        Args:
            content: メッセージ内容
            image: 画像データ（オプション）
            model_name: 使用モデル名
            
        Returns:
            メッセージID
        """
        if not self._current_session_id:
            self.start_new_session(model_name)
        
        return self.db.save_message(
            session_id=self._current_session_id,
            role="user",
            content=content,
            image=image,
            model_name=model_name
        )
    
    def save_assistant_message(self, content: str) -> int:
        """
        アシスタントメッセージを保存
        
        Args:
            content: メッセージ内容
            
        Returns:
            メッセージID
        """
        if not self._current_session_id:
            logger.warning("セッションが設定されていません。新しいセッションを開始します。")
            self.start_new_session()
        
        return self.db.save_message(
            session_id=self._current_session_id,
            role="assistant",
            content=content
        )
    
    def load_session_messages(self, session_id: Optional[str] = None, 
                            limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        セッションのメッセージを読み込み
        
        Args:
            session_id: セッションID（指定しない場合は現在のセッション）
            limit: 取得するメッセージ数の上限
            
        Returns:
            メッセージのリスト（Streamlit形式）
        """
        if session_id is None:
            session_id = self._current_session_id
        
        if session_id is None:
            return []
        
        messages = self.db.load_messages(session_id, limit)
        
        # Streamlit形式に変換
        streamlit_messages = []
        for msg in messages:
            streamlit_msg = {
                "role": msg["role"],
                "content": msg["content"]
            }
            
            # 画像データがある場合は追加
            if "image" in msg:
                streamlit_msg["image"] = msg["image"]
            
            streamlit_messages.append(streamlit_msg)
        
        logger.debug(f"セッションメッセージ読み込み: session_id={session_id}, count={len(streamlit_messages)}")
        return streamlit_messages
    
    def search_messages(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        メッセージを検索
        
        Args:
            query: 検索クエリ
            limit: 結果の上限数
            
        Returns:
            検索結果のリスト
        """
        return self.db.search_messages(query, limit)
    
    def get_conversation_list(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        会話一覧を取得
        
        Args:
            limit: 取得数の上限
            
        Returns:
            会話一覧
        """
        return self.db.get_conversations(limit)
    
    def delete_conversation(self, session_id: str) -> bool:
        """
        指定した会話を削除
        
        Args:
            session_id: セッションID
            
        Returns:
            削除の成功可否
        """
        success = self.db.delete_conversation(session_id)
        
        # 現在のセッションが削除された場合はクリア
        if success and self._current_session_id == session_id:
            self._current_session_id = None
            logger.info("現在のセッションが削除されました")
        
        return success
    
    def clear_all_history(self) -> bool:
        """
        全ての履歴を削除
        
        Returns:
            削除の成功可否
        """
        success = self.db.clear_all_history()
        if success:
            self._current_session_id = None
            logger.info("全履歴削除完了")
        return success
    
    def export_conversation(self, session_id: str, format: str = "json") -> Optional[str]:
        """
        会話をエクスポート
        
        Args:
            session_id: セッションID
            format: エクスポート形式（"json", "text", "markdown"）
            
        Returns:
            エクスポートされたデータ（失敗時はNone）
        """
        messages = self.db.load_messages(session_id)
        if not messages:
            return None
        
        if format == "json":
            import json
            return json.dumps(messages, ensure_ascii=False, indent=2, default=str)
        
        elif format == "text":
            lines = []
            for msg in messages:
                timestamp = msg.get("timestamp", "")
                role = "ユーザー" if msg["role"] == "user" else "アシスタント"
                lines.append(f"[{timestamp}] {role}: {msg['content']}")
                if "image" in msg:
                    lines.append("  (画像あり)")
            return "\n".join(lines)
        
        elif format == "markdown":
            lines = []
            for msg in messages:
                timestamp = msg.get("timestamp", "")
                role = "👤 ユーザー" if msg["role"] == "user" else "🤖 アシスタント"
                lines.append(f"## {role} ({timestamp})")
                lines.append(msg['content'])
                if "image" in msg:
                    lines.append("*📷 画像あり*")
                lines.append("")
            return "\n".join(lines)
        
        else:
            logger.error(f"サポートされていないエクスポート形式: {format}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        履歴の統計情報を取得
        
        Returns:
            統計情報
        """
        db_info = self.db.get_database_info()
        
        # 追加の統計情報
        stats = {
            **db_info,
            "current_session_id": self._current_session_id,
            "database_size_mb": round(db_info["database_size_bytes"] / (1024 * 1024), 2)
        }
        
        return stats
    
    def migrate_session_state(self, session_state_messages: List[Dict[str, Any]], 
                            model_name: str = None) -> str:
        """
        Streamlitのセッション状態からデータベースに履歴を移行
        
        Args:
            session_state_messages: st.session_state.messagesの内容
            model_name: 使用していたモデル名
            
        Returns:
            作成されたセッションID
        """
        if not session_state_messages:
            return self.start_new_session(model_name)
        
        session_id = self.start_new_session(model_name)
        
        for msg in session_state_messages:
            role = msg["role"]
            content = msg["content"]
            image = msg.get("image")
            
            self.db.save_message(
                session_id=session_id,
                role=role,
                content=content,
                image=image,
                model_name=model_name if role == "user" else None
            )
        
        logger.info(f"セッション状態を移行: {len(session_state_messages)}メッセージ -> {session_id}")
        return session_id