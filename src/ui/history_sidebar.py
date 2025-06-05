"""
チャット履歴管理のためのサイドバーUIコンポーネント
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..utils.history_manager import ChatHistoryManager

logger = logging.getLogger(__name__)

def render_history_sidebar(history_manager: ChatHistoryManager) -> Optional[str]:
    """
    履歴管理サイドバーを描画
    
    Args:
        history_manager: 履歴管理マネージャー
        
    Returns:
        選択された会話のセッションID（選択されていない場合はNone）
    """
    try:
        st.subheader("📚 チャット履歴")
        
        # 会話一覧表示
        selected_session_id = _render_conversation_list(history_manager)
        
        # 履歴管理操作
        st.divider()
        _render_history_actions(history_manager)
        
        return selected_session_id
    
    except Exception as e:
        logger.error(f"履歴サイドバー描画エラー: {e}")
        st.error(f"履歴機能でエラーが発生しました: {e}")
        return None

def _render_conversation_list(history_manager: ChatHistoryManager) -> Optional[str]:
    """
    会話一覧を描画
    
    Args:
        history_manager: 履歴管理マネージャー
        
    Returns:
        選択された会話のセッションID
    """
    conversations = history_manager.get_conversation_list(limit=20)
    
    if not conversations:
        st.info("💬 まだ保存された会話がありません")
        return None
    
    selected_session_id = None
    
    for conv in conversations:
        session_id = conv["session_id"]
        title = conv["title"] or "無題の会話"
        model_name = conv["model_name"] or "不明"
        message_count = conv["message_count"]
        updated_at = conv["updated_at"]
        
        # 日時をフォーマット
        try:
            dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%m/%d %H:%M")
        except:
            formatted_time = "不明"
        
        # 会話表示
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # タイトルを短縮
            display_title = title[:30] + "..." if len(title) > 30 else title
            
            if st.button(
                f"💬 {display_title}",
                key=f"conv_{session_id}",
                help=f"モデル: {model_name}\\nメッセージ数: {message_count}\\n更新: {formatted_time}",
                use_container_width=True
            ):
                selected_session_id = session_id
        
        with col2:
            if st.button("🗑️", key=f"del_{session_id}", help="削除"):
                if st.session_state.get(f"confirm_delete_{session_id}", False):
                    history_manager.delete_conversation(session_id)
                    st.success("会話を削除しました")
                    st.rerun()
                else:
                    st.session_state[f"confirm_delete_{session_id}"] = True
                    st.warning("もう一度クリックして削除を確認してください")
                    st.rerun()
        
        # メタ情報を小さく表示
        st.caption(f"🤖 {model_name} • 💬 {message_count}件 • 🕒 {formatted_time}")
        st.divider()
    
    return selected_session_id

def _render_search_interface(history_manager: ChatHistoryManager):
    """
    検索インターフェースを描画
    
    Args:
        history_manager: 履歴管理マネージャー
    """
    search_query = st.text_input("🔍 メッセージを検索", placeholder="検索キーワードを入力...")
    
    if search_query:
        results = history_manager.search_messages(search_query, limit=10)
        
        if results:
            st.write(f"**{len(results)}件の結果**")
            
            for result in results:
                with st.expander(
                    f"💬 {result['title'][:40]}..." if result['title'] else "無題の会話",
                    expanded=False
                ):
                    st.write(f"**{result['role']}**: {result['content'][:200]}...")
                    st.caption(f"モデル: {result['model_name']} • 日時: {result['timestamp']}")
                    
                    # 会話を開くボタン
                    if st.button(f"この会話を開く", key=f"open_{result['session_id']}_{result['timestamp']}"):
                        # セッション状態に選択された会話を設定
                        st.session_state["selected_conversation"] = result['session_id']
                        st.rerun()
        else:
            st.info("🔍 検索結果が見つかりませんでした")

def _render_statistics(history_manager: ChatHistoryManager):
    """
    統計情報を描画
    
    Args:
        history_manager: 履歴管理マネージャー
    """
    stats = history_manager.get_statistics()
    
    # メトリクス表示
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("📊 総会話数", stats["conversation_count"])
        st.metric("💬 総メッセージ数", stats["message_count"])
    
    with col2:
        st.metric("🖼️ 画像メッセージ", stats["image_message_count"])
        st.metric("💾 DB サイズ", f"{stats['database_size_mb']} MB")
    
    # 現在のセッション情報
    if stats["current_session_id"]:
        st.info(f"📍 現在のセッション: {stats['current_session_id'][:8]}...")
    else:
        st.info("📍 新しいセッションです")
    
    # データベース情報
    with st.expander("🗄️ データベース詳細"):
        st.code(f"パス: {stats['database_path']}")
        st.code(f"サイズ: {stats['database_size_bytes']:,} bytes")

def _render_history_actions(history_manager: ChatHistoryManager):
    """
    履歴管理アクションを描画
    
    Args:
        history_manager: 履歴管理マネージャー
    """
    st.subheader("🔧 履歴管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🆕 新しい会話", use_container_width=True):
            # 現在のセッションを保存してから新しいセッションを開始
            if st.session_state.get("messages"):
                current_model = st.session_state.get("selected_model")
                history_manager.migrate_session_state(st.session_state.messages, current_model)
            
            # 新しいセッションを開始
            new_session_id = history_manager.start_new_session()
            st.session_state.messages = []
            st.session_state["current_session_id"] = new_session_id
            st.success("新しい会話を開始しました")
            st.rerun()
    
    with col2:
        if st.button("💾 現在の会話を保存", use_container_width=True):
            if st.session_state.get("messages"):
                current_model = st.session_state.get("selected_model")
                session_id = history_manager.migrate_session_state(st.session_state.messages, current_model)
                st.session_state["current_session_id"] = session_id
                st.success("会話を保存しました")
            else:
                st.warning("保存する会話がありません")
    
    # エクスポート機能
    if st.button("📤 現在の会話をエクスポート", use_container_width=True):
        _render_export_interface(history_manager)
    
    # 危険な操作
    with st.expander("⚠️ 危険な操作"):
        st.warning("以下の操作は元に戻せません")
        
        if st.button("🗑️ 全履歴を削除", type="secondary"):
            if st.session_state.get("confirm_clear_all", False):
                if history_manager.clear_all_history():
                    st.session_state.messages = []
                    st.session_state["current_session_id"] = None
                    st.success("全履歴を削除しました")
                    st.rerun()
                else:
                    st.error("履歴削除に失敗しました")
            else:
                st.session_state["confirm_clear_all"] = True
                st.warning("もう一度クリックして削除を確認してください")

def _render_export_interface(history_manager: ChatHistoryManager):
    """
    エクスポートインターフェースを描画
    
    Args:
        history_manager: 履歴管理マネージャー
    """
    current_session_id = history_manager.get_current_session_id()
    
    if not current_session_id:
        st.warning("エクスポートする会話がありません")
        return
    
    format_options = {
        "json": "JSON形式",
        "text": "テキスト形式", 
        "markdown": "Markdown形式"
    }
    
    selected_format = st.selectbox("エクスポート形式", list(format_options.keys()), 
                                 format_func=lambda x: format_options[x])
    
    if st.button("エクスポート実行"):
        exported_data = history_manager.export_conversation(current_session_id, selected_format)
        
        if exported_data:
            st.download_button(
                label="💾 ダウンロード",
                data=exported_data,
                file_name=f"chat_export_{current_session_id[:8]}.{selected_format}",
                mime="text/plain" if selected_format in ["text", "markdown"] else "application/json"
            )
        else:
            st.error("エクスポートに失敗しました")

def load_conversation_if_selected(history_manager: ChatHistoryManager) -> bool:
    """
    選択された会話があれば読み込む
    
    Args:
        history_manager: 履歴管理マネージャー
        
    Returns:
        会話が読み込まれたかどうか
    """
    selected_conversation = st.session_state.get("selected_conversation")
    
    if selected_conversation:
        messages = history_manager.load_session_messages(selected_conversation)
        if messages:
            st.session_state.messages = messages
            st.session_state["current_session_id"] = selected_conversation
            history_manager.set_current_session(selected_conversation)
            
            # 選択状態をクリア
            del st.session_state["selected_conversation"]
            
            st.success(f"会話を読み込みました ({len(messages)}メッセージ)")
            st.rerun()
            return True
    
    return False