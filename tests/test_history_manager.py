"""
チャット履歴管理マネージャーのテスト
"""

import pytest
import tempfile
import os
from PIL import Image

from src.utils.history_manager import ChatHistoryManager

@pytest.fixture
def temp_manager():
    """テスト用の一時履歴マネージャー"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    manager = ChatHistoryManager(db_path)
    yield manager
    
    # クリーンアップ
    if os.path.exists(db_path):
        os.unlink(db_path)

@pytest.fixture
def sample_image():
    """テスト用のサンプル画像"""
    image = Image.new('RGB', (100, 100), color='blue')
    return image

class TestChatHistoryManager:
    """ChatHistoryManagerのテストクラス"""
    
    def test_start_new_session(self, temp_manager):
        """新しいセッション開始のテスト"""
        session_id = temp_manager.start_new_session("GPT-4o")
        
        assert session_id is not None
        assert len(session_id) > 0
        assert temp_manager.get_current_session_id() == session_id
    
    def test_set_current_session(self, temp_manager):
        """現在のセッション設定のテスト"""
        test_session_id = "test_session_123"
        temp_manager.set_current_session(test_session_id)
        
        assert temp_manager.get_current_session_id() == test_session_id
    
    def test_save_and_load_user_message(self, temp_manager):
        """ユーザーメッセージの保存・読み込みテスト"""
        content = "こんにちは！"
        model_name = "GPT-4o"
        
        # メッセージ保存
        message_id = temp_manager.save_user_message(content, model_name=model_name)
        assert message_id > 0
        
        # セッションが自動作成されているはず
        session_id = temp_manager.get_current_session_id()
        assert session_id is not None
        
        # メッセージ読み込み
        messages = temp_manager.load_session_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == content
    
    def test_save_and_load_image_message(self, temp_manager, sample_image):
        """画像付きメッセージの保存・読み込みテスト"""
        content = "この画像について教えて"
        
        # 画像付きメッセージ保存
        message_id = temp_manager.save_user_message(content, sample_image)
        assert message_id > 0
        
        # メッセージ読み込み
        messages = temp_manager.load_session_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == content
        assert "image" in messages[0]
    
    def test_save_assistant_message(self, temp_manager):
        """アシスタントメッセージの保存テスト"""
        # 先にセッションを開始
        temp_manager.start_new_session()
        
        content = "こんにちは！何かお手伝いできることはありますか？"
        message_id = temp_manager.save_assistant_message(content)
        assert message_id > 0
        
        # メッセージ読み込み
        messages = temp_manager.load_session_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "assistant"
        assert messages[0]["content"] == content
    
    def test_conversation_flow(self, temp_manager):
        """会話の流れのテスト"""
        model_name = "Claude Sonnet 4"
        
        # ユーザーメッセージ
        temp_manager.save_user_message("プログラミングを学びたいです", model_name=model_name)
        
        # アシスタントメッセージ
        temp_manager.save_assistant_message("素晴らしいですね！どの言語から始めたいですか？")
        
        # 2番目のユーザーメッセージ
        temp_manager.save_user_message("Pythonを学びたいです")
        
        # 2番目のアシスタントメッセージ
        temp_manager.save_assistant_message("Pythonは初心者に優しい言語です。基本から始めましょう。")
        
        # メッセージ読み込み
        messages = temp_manager.load_session_messages()
        assert len(messages) == 4
        
        # 順序確認
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert messages[2]["role"] == "user"
        assert messages[3]["role"] == "assistant"
    
    def test_search_messages(self, temp_manager):
        """メッセージ検索のテスト"""
        # テストデータ作成
        temp_manager.save_user_message("Pythonについて教えて", model_name="GPT-4o")
        temp_manager.save_assistant_message("Pythonはプログラミング言語です")
        temp_manager.save_user_message("JavaScriptも知りたい")
        temp_manager.save_assistant_message("JavaScriptはWebの言語です")
        
        # 検索実行
        results = temp_manager.search_messages("Python")
        assert len(results) == 2
        
        results = temp_manager.search_messages("JavaScript")
        assert len(results) == 2
        
        results = temp_manager.search_messages("存在しない")
        assert len(results) == 0
    
    def test_get_conversation_list(self, temp_manager):
        """会話一覧取得のテスト"""
        # 複数の会話を作成
        # 会話1
        temp_manager.start_new_session("GPT-4o")
        temp_manager.save_user_message("会話1のメッセージ")
        
        # 会話2
        temp_manager.start_new_session("Claude Sonnet 4")
        temp_manager.save_user_message("会話2のメッセージ")
        
        # 会話一覧取得
        conversations = temp_manager.get_conversation_list()
        assert len(conversations) >= 2
        
        # 最新の会話が先頭にあるはず
        latest_conv = conversations[0]
        assert "session_id" in latest_conv
        assert "title" in latest_conv
        assert "model_name" in latest_conv
    
    def test_delete_conversation(self, temp_manager):
        """会話削除のテスト"""
        # 会話作成
        session_id = temp_manager.start_new_session()
        temp_manager.save_user_message("削除予定のメッセージ")
        
        # 削除前は存在する
        messages = temp_manager.load_session_messages()
        assert len(messages) == 1
        
        # 削除実行
        result = temp_manager.delete_conversation(session_id)
        assert result is True
        
        # 現在のセッションIDがクリアされているはず
        assert temp_manager.get_current_session_id() is None
    
    def test_clear_all_history(self, temp_manager):
        """全履歴削除のテスト"""
        # データ作成
        temp_manager.save_user_message("メッセージ1")
        temp_manager.start_new_session()
        temp_manager.save_user_message("メッセージ2")
        
        # 削除前は存在する
        conversations = temp_manager.get_conversation_list()
        assert len(conversations) >= 2
        
        # 全削除実行
        result = temp_manager.clear_all_history()
        assert result is True
        
        # 削除後は空
        conversations = temp_manager.get_conversation_list()
        assert len(conversations) == 0
        
        # 現在のセッションIDもクリアされているはず
        assert temp_manager.get_current_session_id() is None
    
    def test_export_conversation_json(self, temp_manager):
        """会話エクスポート（JSON）のテスト"""
        # 会話作成
        session_id = temp_manager.start_new_session()
        temp_manager.save_user_message("テストメッセージ")
        temp_manager.save_assistant_message("テスト応答")
        
        # JSON形式でエクスポート
        exported_data = temp_manager.export_conversation(session_id, "json")
        assert exported_data is not None
        assert "テストメッセージ" in exported_data
        assert "テスト応答" in exported_data
        
        # JSONとしてパースできるかチェック
        import json
        parsed_data = json.loads(exported_data)
        assert isinstance(parsed_data, list)
        assert len(parsed_data) == 2
    
    def test_export_conversation_text(self, temp_manager):
        """会話エクスポート（テキスト）のテスト"""
        session_id = temp_manager.start_new_session()
        temp_manager.save_user_message("テストメッセージ")
        temp_manager.save_assistant_message("テスト応答")
        
        # テキスト形式でエクスポート
        exported_data = temp_manager.export_conversation(session_id, "text")
        assert exported_data is not None
        assert "ユーザー" in exported_data
        assert "アシスタント" in exported_data
        assert "テストメッセージ" in exported_data
        assert "テスト応答" in exported_data
    
    def test_export_conversation_markdown(self, temp_manager):
        """会話エクスポート（Markdown）のテスト"""
        session_id = temp_manager.start_new_session()
        temp_manager.save_user_message("テストメッセージ")
        temp_manager.save_assistant_message("テスト応答")
        
        # Markdown形式でエクスポート
        exported_data = temp_manager.export_conversation(session_id, "markdown")
        assert exported_data is not None
        assert "## 👤 ユーザー" in exported_data
        assert "## 🤖 アシスタント" in exported_data
        assert "テストメッセージ" in exported_data
        assert "テスト応答" in exported_data
    
    def test_get_statistics(self, temp_manager):
        """統計情報取得のテスト"""
        # データ作成
        temp_manager.save_user_message("統計テスト")
        temp_manager.save_assistant_message("統計応答")
        
        stats = temp_manager.get_statistics()
        
        assert "conversation_count" in stats
        assert "message_count" in stats
        assert "current_session_id" in stats
        assert "database_size_mb" in stats
        
        assert stats["conversation_count"] >= 1
        assert stats["message_count"] >= 2
    
    def test_migrate_session_state(self, temp_manager):
        """セッション状態移行のテスト"""
        # Streamlitのセッション状態を模擬
        session_state_messages = [
            {"role": "user", "content": "移行テスト1"},
            {"role": "assistant", "content": "移行応答1"},
            {"role": "user", "content": "移行テスト2"},
            {"role": "assistant", "content": "移行応答2"}
        ]
        
        # 移行実行
        session_id = temp_manager.migrate_session_state(session_state_messages, "GPT-4o")
        
        assert session_id is not None
        assert temp_manager.get_current_session_id() == session_id
        
        # メッセージが正しく移行されているかチェック
        messages = temp_manager.load_session_messages()
        assert len(messages) == 4
        
        for i, msg in enumerate(messages):
            assert msg["role"] == session_state_messages[i]["role"]
            assert msg["content"] == session_state_messages[i]["content"]
    
    def test_load_specific_session(self, temp_manager):
        """特定セッション読み込みのテスト"""
        # セッション1
        session_id_1 = temp_manager.start_new_session()
        temp_manager.save_user_message("セッション1のメッセージ")
        
        # セッション2
        session_id_2 = temp_manager.start_new_session()
        temp_manager.save_user_message("セッション2のメッセージ")
        
        # セッション1のメッセージを読み込み
        messages_1 = temp_manager.load_session_messages(session_id_1)
        assert len(messages_1) == 1
        assert messages_1[0]["content"] == "セッション1のメッセージ"
        
        # セッション2のメッセージを読み込み
        messages_2 = temp_manager.load_session_messages(session_id_2)
        assert len(messages_2) == 1
        assert messages_2[0]["content"] == "セッション2のメッセージ"