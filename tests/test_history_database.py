"""
チャット履歴データベースのテスト
"""

import pytest
import tempfile
import os
from pathlib import Path
from PIL import Image
import io

from src.utils.database import ChatHistoryDatabase

@pytest.fixture
def temp_db():
    """テスト用の一時データベース"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    db = ChatHistoryDatabase(db_path)
    yield db
    
    # クリーンアップ
    if os.path.exists(db_path):
        os.unlink(db_path)

@pytest.fixture
def sample_image():
    """テスト用のサンプル画像"""
    image = Image.new('RGB', (100, 100), color='red')
    return image

class TestChatHistoryDatabase:
    """ChatHistoryDatabaseのテストクラス"""
    
    def test_init_database(self, temp_db):
        """データベース初期化のテスト"""
        assert temp_db.db_path.exists()
        
        # テーブルが作成されているかチェック
        import sqlite3
        with sqlite3.connect(temp_db.db_path) as conn:
            cursor = conn.cursor()
            
            # conversationsテーブル
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'")
            assert cursor.fetchone() is not None
            
            # messagesテーブル
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
            assert cursor.fetchone() is not None
    
    def test_create_conversation(self, temp_db):
        """会話作成のテスト"""
        session_id = "test_session_1"
        title = "テスト会話"
        model_name = "GPT-4o"
        
        conversation_id = temp_db.create_conversation(session_id, title, model_name)
        assert isinstance(conversation_id, int)
        assert conversation_id > 0
        
        # 重複作成はエラーになるはず
        with pytest.raises(Exception):
            temp_db.create_conversation(session_id, title, model_name)
    
    def test_get_conversation_id(self, temp_db):
        """会話ID取得のテスト"""
        session_id = "test_session_2"
        
        # 存在しない場合はNone
        assert temp_db.get_conversation_id(session_id) is None
        
        # 作成後は取得できる
        conversation_id = temp_db.create_conversation(session_id)
        assert temp_db.get_conversation_id(session_id) == conversation_id
    
    def test_save_and_load_text_message(self, temp_db):
        """テキストメッセージの保存・読み込みテスト"""
        session_id = "test_session_3"
        content = "こんにちは、テストメッセージです。"
        
        # メッセージ保存
        message_id = temp_db.save_message(session_id, "user", content)
        assert isinstance(message_id, int)
        assert message_id > 0
        
        # メッセージ読み込み
        messages = temp_db.load_messages(session_id)
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == content
        assert "image" not in messages[0]
    
    def test_save_and_load_image_message(self, temp_db, sample_image):
        """画像メッセージの保存・読み込みテスト"""
        session_id = "test_session_4"
        content = "画像付きメッセージです。"
        
        # 画像付きメッセージ保存
        message_id = temp_db.save_message(session_id, "user", content, sample_image)
        assert message_id > 0
        
        # メッセージ読み込み
        messages = temp_db.load_messages(session_id)
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == content
        assert "image" in messages[0]
        
        # 画像が正しく復元されているか
        restored_image = messages[0]["image"]
        assert isinstance(restored_image, Image.Image)
        assert restored_image.size == sample_image.size
    
    def test_multiple_messages(self, temp_db):
        """複数メッセージのテスト"""
        session_id = "test_session_5"
        
        # 複数メッセージを保存
        temp_db.save_message(session_id, "user", "最初のメッセージ")
        temp_db.save_message(session_id, "assistant", "応答メッセージ")
        temp_db.save_message(session_id, "user", "2番目のメッセージ")
        
        # 読み込み
        messages = temp_db.load_messages(session_id)
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert messages[2]["role"] == "user"
    
    def test_search_messages(self, temp_db):
        """メッセージ検索のテスト"""
        session_id = "test_session_6"
        
        # 検索対象メッセージを作成
        temp_db.save_message(session_id, "user", "プログラミングについて教えて")
        temp_db.save_message(session_id, "assistant", "プログラミングは...")
        temp_db.save_message(session_id, "user", "料理のレシピを知りたい")
        
        # 検索実行
        results = temp_db.search_messages("プログラミング")
        assert len(results) == 2
        
        results = temp_db.search_messages("料理")
        assert len(results) == 1
        
        results = temp_db.search_messages("存在しないキーワード")
        assert len(results) == 0
    
    def test_search_messages_sql_injection_protection(self, temp_db):
        """SQLインジェクション攻撃の防止テスト"""
        session_id = "test_session_sql_injection"
        
        # 正常なメッセージを保存
        temp_db.save_message(session_id, "user", "正常なメッセージです")
        temp_db.save_message(session_id, "assistant", "こんにちは")
        
        # SQLインジェクション攻撃のテストケース
        malicious_queries = [
            "'; DROP TABLE messages; --",
            "' OR '1'='1",
            "'; DELETE FROM conversations; --",
            "' UNION SELECT session_id FROM conversations --",
            "%'; INSERT INTO messages (content) VALUES ('hacked'); --",
        ]
        
        for malicious_query in malicious_queries:
            # 攻撃クエリが正しく処理され、エラーが発生しないことを確認
            results = temp_db.search_messages(malicious_query)
            # 結果が空またはエラーが発生しないことを確認
            assert isinstance(results, list)
        
        # データベースが破損していないことを確認
        all_messages = temp_db.load_messages(session_id)
        assert len(all_messages) == 2  # 元のメッセージがそのまま残っている
        
        # LIKE句特殊文字のエスケープテスト
        temp_db.save_message(session_id, "user", "100%完了しました")
        temp_db.save_message(session_id, "user", "test_value検索")
        
        # % や _ を含む検索が正しく動作することを確認
        results = temp_db.search_messages("100%")
        assert len(results) == 1
        assert "100%完了しました" in results[0]["content"]
        
        results = temp_db.search_messages("test_value")
        assert len(results) == 1
        assert "test_value検索" in results[0]["content"]
    
    def test_get_conversations(self, temp_db):
        """会話一覧取得のテスト"""
        # 複数の会話を作成
        temp_db.save_message("session_1", "user", "会話1")
        temp_db.save_message("session_2", "user", "会話2")
        temp_db.save_message("session_3", "user", "会話3")
        
        conversations = temp_db.get_conversations()
        assert len(conversations) == 3
        
        # フィールドが含まれているかチェック
        conv = conversations[0]
        assert "session_id" in conv
        assert "title" in conv
        assert "message_count" in conv
        assert "created_at" in conv
        assert "updated_at" in conv
    
    def test_delete_conversation(self, temp_db):
        """会話削除のテスト"""
        session_id = "test_session_7"
        
        # メッセージを保存
        temp_db.save_message(session_id, "user", "削除テスト")
        
        # 削除前は存在する
        assert temp_db.get_conversation_id(session_id) is not None
        messages = temp_db.load_messages(session_id)
        assert len(messages) == 1
        
        # 削除実行
        result = temp_db.delete_conversation(session_id)
        assert result is True
        
        # 削除後は存在しない
        assert temp_db.get_conversation_id(session_id) is None
        messages = temp_db.load_messages(session_id)
        assert len(messages) == 0
    
    def test_clear_all_history(self, temp_db):
        """全履歴削除のテスト"""
        # 複数の会話を作成
        temp_db.save_message("session_1", "user", "メッセージ1")
        temp_db.save_message("session_2", "user", "メッセージ2")
        
        # 削除前は存在する
        conversations = temp_db.get_conversations()
        assert len(conversations) == 2
        
        # 全削除実行
        result = temp_db.clear_all_history()
        assert result is True
        
        # 削除後は空
        conversations = temp_db.get_conversations()
        assert len(conversations) == 0
    
    def test_get_database_info(self, temp_db):
        """データベース情報取得のテスト"""
        # いくつかのデータを追加
        temp_db.save_message("session_1", "user", "テストメッセージ", None)
        temp_db.save_message("session_1", "assistant", "応答")
        
        info = temp_db.get_database_info()
        
        assert "conversation_count" in info
        assert "message_count" in info
        assert "image_message_count" in info
        assert "database_size_bytes" in info
        assert "database_path" in info
        
        assert info["conversation_count"] == 1
        assert info["message_count"] == 2
        assert info["image_message_count"] == 0
        assert info["database_size_bytes"] > 0
    
    def test_message_limit(self, temp_db):
        """メッセージ制限のテスト"""
        session_id = "test_session_8"
        
        # 10個のメッセージを作成
        for i in range(10):
            temp_db.save_message(session_id, "user", f"メッセージ {i}")
        
        # 制限なしで全て取得
        all_messages = temp_db.load_messages(session_id)
        assert len(all_messages) == 10
        
        # 制限ありで取得
        limited_messages = temp_db.load_messages(session_id, limit=5)
        assert len(limited_messages) == 5
        
        # 最初の5件が取得されるはず
        for i in range(5):
            assert limited_messages[i]["content"] == f"メッセージ {i}"