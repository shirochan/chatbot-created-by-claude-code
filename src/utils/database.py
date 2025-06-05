"""
チャット履歴を管理するためのデータベースモジュール
SQLiteを使用してチャット履歴を永続化する
"""

import sqlite3
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

class ChatHistoryDatabase:
    """チャット履歴データベース管理クラス"""
    
    def __init__(self, db_path: str = "chat_history.db"):
        """
        データベース初期化
        
        Args:
            db_path: データベースファイルのパス
        """
        self.db_path = Path(db_path)
        self.init_database()
    
    def init_database(self):
        """データベーステーブルを初期化"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # conversationsテーブル（会話セッション管理）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    title TEXT,
                    model_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # messagesテーブル（メッセージ管理）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    has_image BOOLEAN DEFAULT FALSE,
                    image_data TEXT,
                    image_format TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            ''')
            
            # インデックス作成
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_conversations_session_id 
                ON conversations(session_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
                ON messages(conversation_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
                ON messages(timestamp)
            ''')
            
            conn.commit()
            logger.info(f"データベース初期化完了: {self.db_path}")
    
    def create_conversation(self, session_id: str, title: str = None, model_name: str = None) -> int:
        """
        新しい会話セッションを作成
        
        Args:
            session_id: セッションID
            title: 会話タイトル
            model_name: 使用モデル名
            
        Returns:
            作成された会話のID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversations (session_id, title, model_name)
                VALUES (?, ?, ?)
            ''', (session_id, title, model_name))
            conversation_id = cursor.lastrowid
            conn.commit()
            logger.debug(f"新しい会話作成: ID={conversation_id}, session_id={session_id}")
            return conversation_id
    
    def get_conversation_id(self, session_id: str) -> Optional[int]:
        """
        セッションIDから会話IDを取得
        
        Args:
            session_id: セッションID
            
        Returns:
            会話ID（存在しない場合はNone）
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM conversations WHERE session_id = ?
            ''', (session_id,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def save_message(self, session_id: str, role: str, content: str, 
                    image: Optional[Image.Image] = None, model_name: str = None) -> int:
        """
        メッセージを保存
        
        Args:
            session_id: セッションID
            role: メッセージの役割（'user' または 'assistant'）
            content: メッセージ内容
            image: 画像データ（オプション）
            model_name: 使用モデル名（会話作成時のみ）
            
        Returns:
            保存されたメッセージのID
        """
        # 会話IDを取得または作成
        conversation_id = self.get_conversation_id(session_id)
        if conversation_id is None:
            # タイトルは最初のユーザーメッセージから生成
            title = content[:50] + "..." if len(content) > 50 else content
            conversation_id = self.create_conversation(session_id, title, model_name)
        
        # 画像データを処理
        image_data = None
        image_format = None
        has_image = False
        
        if image is not None:
            has_image = True
            image_format = image.format or "PNG"
            
            # 画像をbase64エンコード
            buffer = io.BytesIO()
            image.save(buffer, format=image_format)
            image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO messages (conversation_id, role, content, has_image, image_data, image_format)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (conversation_id, role, content, has_image, image_data, image_format))
            
            # 会話の更新日時を更新
            cursor.execute('''
                UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
            ''', (conversation_id,))
            
            message_id = cursor.lastrowid
            conn.commit()
            
            logger.debug(f"メッセージ保存: ID={message_id}, role={role}, has_image={has_image}")
            return message_id
    
    def load_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        セッションのメッセージを読み込み
        
        Args:
            session_id: セッションID
            limit: 取得するメッセージ数の上限
            
        Returns:
            メッセージのリスト
        """
        conversation_id = self.get_conversation_id(session_id)
        if conversation_id is None:
            return []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT role, content, has_image, image_data, image_format, timestamp
                FROM messages 
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
            '''
            
            params = [conversation_id]
            if limit:
                query += ' LIMIT ?'
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            messages = []
            for row in rows:
                role, content, has_image, image_data, _, timestamp = row
                
                message = {
                    "role": role,
                    "content": content,
                    "timestamp": timestamp
                }
                
                # 画像データを復元
                if has_image and image_data:
                    try:
                        image_bytes = base64.b64decode(image_data)
                        image = Image.open(io.BytesIO(image_bytes))
                        message["image"] = image
                    except Exception as e:
                        logger.error(f"画像データの復元に失敗: {e}")
                
                messages.append(message)
            
            logger.debug(f"メッセージ読み込み: session_id={session_id}, count={len(messages)}")
            return messages
    
    def search_messages(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        メッセージを検索
        
        Args:
            query: 検索クエリ
            limit: 結果の上限数
            
        Returns:
            検索結果のリスト
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.session_id, c.title, c.model_name, m.role, m.content, m.timestamp
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE m.content LIKE ?
                ORDER BY m.timestamp DESC
                LIMIT ?
            ''', (f'%{query}%', limit))
            
            results = []
            for row in cursor.fetchall():
                session_id, title, model_name, role, content, timestamp = row
                results.append({
                    "session_id": session_id,
                    "title": title,
                    "model_name": model_name,
                    "role": role,
                    "content": content,
                    "timestamp": timestamp
                })
            
            logger.debug(f"メッセージ検索: query='{query}', results={len(results)}")
            return results
    
    def get_conversations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        会話一覧を取得
        
        Args:
            limit: 取得数の上限
            
        Returns:
            会話一覧
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT session_id, title, model_name, created_at, updated_at,
                       (SELECT COUNT(*) FROM messages WHERE conversation_id = conversations.id) as message_count
                FROM conversations
                ORDER BY updated_at DESC
                LIMIT ?
            ''', (limit,))
            
            conversations = []
            for row in cursor.fetchall():
                session_id, title, model_name, created_at, updated_at, message_count = row
                conversations.append({
                    "session_id": session_id,
                    "title": title,
                    "model_name": model_name,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "message_count": message_count
                })
            
            return conversations
    
    def delete_conversation(self, session_id: str) -> bool:
        """
        会話を削除
        
        Args:
            session_id: セッションID
            
        Returns:
            削除の成功可否
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM conversations WHERE session_id = ?
            ''', (session_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            
            if deleted:
                logger.info(f"会話削除: session_id={session_id}")
            return deleted
    
    def clear_all_history(self) -> bool:
        """
        全ての履歴を削除
        
        Returns:
            削除の成功可否
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM messages')
                cursor.execute('DELETE FROM conversations')
                conn.commit()
                logger.info("全履歴削除完了")
                return True
        except Exception as e:
            logger.error(f"履歴削除エラー: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        データベース情報を取得
        
        Returns:
            データベース統計情報
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 会話数
            cursor.execute('SELECT COUNT(*) FROM conversations')
            conversation_count = cursor.fetchone()[0]
            
            # メッセージ数
            cursor.execute('SELECT COUNT(*) FROM messages')
            message_count = cursor.fetchone()[0]
            
            # 画像付きメッセージ数
            cursor.execute('SELECT COUNT(*) FROM messages WHERE has_image = TRUE')
            image_message_count = cursor.fetchone()[0]
            
            # データベースサイズ
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            return {
                "conversation_count": conversation_count,
                "message_count": message_count,
                "image_message_count": image_message_count,
                "database_size_bytes": db_size,
                "database_path": str(self.db_path)
            }