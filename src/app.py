import streamlit as st
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models import create_model, get_available_models
from src.models.config import ModelConfig
from src.utils import setup_logging, get_app_config, get_logging_config, get_chat_config, get_file_upload_config, get_history_config
from src.utils.file_processing import process_image, process_pdf, get_file_type, format_file_content_for_ai, encode_image_to_base64, get_image_mime_type, sanitize_user_input
from src.utils.history_manager import ChatHistoryManager

# 環境変数の読み込み
load_dotenv()

# 設定の読み込み
app_config = get_app_config()
logging_config = get_logging_config()
chat_config = get_chat_config()
file_upload_config = get_file_upload_config()
history_config = get_history_config()

# ログ設定
logger = setup_logging(
    level=logging_config.get("level", "INFO"), 
    logger_name="chatbot"
)

# 履歴管理の初期化
db_path = history_config.get("database", {}).get("path", "chat_history.db")
history_manager = ChatHistoryManager(db_path)

def show_api_key_error():
    """APIキー未設定時の共通エラーメッセージ"""
    st.error("利用可能なモデルがありません。APIキーを設定してください。")

# ページ設定
st.set_page_config(
    page_title=app_config.get("title", "AIチャットボット"),
    page_icon=app_config.get("page_icon", "🤖"),
    layout=app_config.get("layout", "centered")
)

# タイトル
st.title(f"{app_config.get('page_icon', '🤖')} {app_config.get('title', 'AIチャットボット')}")

# セッション状態の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# 履歴管理のセッション状態初期化
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if "history_initialized" not in st.session_state:
    st.session_state.history_initialized = False

if "available_models" not in st.session_state:
    st.session_state.available_models = get_available_models()

if "selected_model" not in st.session_state:
    if st.session_state.available_models:
        default_model = chat_config.get("default_model", "GPT-4o")
        if default_model in st.session_state.available_models:
            st.session_state.selected_model = default_model
        else:
            st.session_state.selected_model = list(st.session_state.available_models.keys())[0]
    else:
        st.session_state.selected_model = None

# ファイルアップロードリセット用のカウンター
if "file_uploader_key" not in st.session_state:
    st.session_state.file_uploader_key = 0

# サイドバー設定
with st.sidebar:
    # ファイルアップロード機能
    st.header("📁 ファイルアップロード")
    uploaded_file = st.file_uploader(
        "画像またはPDFファイルをアップロード",
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'pdf'],
        help="対応形式: PNG, JPG, JPEG, GIF, BMP, WebP, PDF\nファイルサイズ制限: 画像 10MB、PDF 50MB",
        key=f"file_uploader_{st.session_state.file_uploader_key}"
    )
    
    if uploaded_file is not None:
        file_type = get_file_type(uploaded_file.name, uploaded_file)
        
        if file_type == 'unknown':
            st.error("🚫 不正なファイル形式です。安全でないファイルまたはサポートされていないファイル形式です。")
        else:
            st.success(f"ファイルがアップロードされました: {uploaded_file.name}")
        
        if file_type == 'image':
            # 画像プレビュー表示
            try:
                image, description = process_image(uploaded_file)
                if image:
                    st.image(image, caption=uploaded_file.name, use_container_width=True)
                    with st.expander("画像情報"):
                        st.text(description)
            except Exception as e:
                st.error(f"画像の表示に失敗しました: {e}")
        
        elif file_type == 'pdf':
            # PDFファイル情報表示
            st.info("📄 PDFファイルが選択されています")
            with st.expander("PDFプレビュー"):
                try:
                    # ファイルポインタを先頭に戻す
                    uploaded_file.seek(0)
                    pdf_text = process_pdf(uploaded_file)
                    if pdf_text:
                        # 設定ファイルからプレビュー文字数を取得
                        preview_length = file_upload_config.get("pdf_processing", {}).get("preview_length", 500)
                        preview_text = pdf_text[:preview_length] + "..." if len(pdf_text) > preview_length else pdf_text
                        st.text_area("内容プレビュー", preview_text, height=200, disabled=True)
                    else:
                        st.warning("PDFからテキストを抽出できませんでした")
                except Exception as e:
                    st.error(f"PDFの処理に失敗しました: {e}")
    
    # 区切り線
    st.divider()
    
    # モデル選択をサイドバーに移動
    st.header("⚙️ 設定")
    
    # モデル選択
    available_models = st.session_state.available_models
    if available_models:
        st.subheader("🤖 AIモデル選択")
        
        model_names = list(available_models.keys())
        selected_model = st.selectbox(
            "使用するモデルを選択:",
            model_names,
            index=model_names.index(st.session_state.selected_model) if st.session_state.selected_model in model_names else 0
        )
        
        # モデルが変更された場合
        if selected_model != st.session_state.selected_model:
            st.session_state.selected_model = selected_model
            st.rerun()
        
        # 選択されたモデルの説明を表示
        if selected_model in available_models:
            model_info = available_models[selected_model]
            description = model_info['description']
            supports_vision = model_info.get('supports_vision', False)
            
            if supports_vision:
                st.info(f"📝 {description}\n🖼️ **画像対応**: このモデルは画像を理解できます")
            else:
                st.info(f"📝 {description}\n⚠️ **画像非対応**: このモデルは画像を理解できません（テキスト情報のみ送信）")
    else:
        show_api_key_error()
    
    # 新しい会話を開始
    if st.button("🆕 新しい会話", use_container_width=True):
        # 現在のメッセージをクリア
        st.session_state.messages = []
        # 新しいセッションを開始
        new_session_id = history_manager.start_new_session()
        st.session_state.current_session_id = new_session_id
        st.success("新しい会話を開始しました")
        st.rerun()
    
    # 履歴一覧表示
    st.divider()
    st.subheader("📚 会話履歴")
    
    # 会話一覧を取得
    conversations = history_manager.get_conversation_list(limit=10)
    
    if conversations:
        for conv in conversations:
            session_id = conv["session_id"]
            title = conv["title"] or "無題の会話"
            updated_at = conv["updated_at"]
            message_count = conv["message_count"]
            
            # 日時をフォーマット
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%m/%d %H:%M")
            except:
                formatted_time = "不明"
            
            # タイトルを短縮
            display_title = title[:25] + "..." if len(title) > 25 else title
            
            # 会話選択と削除ボタンを並べたレイアウト
            col1, col2 = st.columns([4, 1])
            
            with col1:
                if st.button(
                    f"💬 {display_title}",
                    key=f"load_conv_{session_id}",
                    help=f"メッセージ数: {message_count}\\n更新: {formatted_time}",
                    use_container_width=True
                ):
                    # 会話を読み込む
                    messages = history_manager.load_session_messages(session_id)
                    if messages:
                        st.session_state.messages = messages
                        st.session_state.current_session_id = session_id
                        history_manager.set_current_session(session_id)
                        st.success(f"会話を読み込みました ({len(messages)}メッセージ)")
                        st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"delete_conv_{session_id}", help="この会話を削除"):
                    # 会話を削除
                    if history_manager.delete_conversation(session_id):
                        # 現在表示中の会話が削除された場合はクリア
                        if st.session_state.current_session_id == session_id:
                            st.session_state.messages = []
                            st.session_state.current_session_id = None
                        st.success("会話を削除しました")
                        st.rerun()
                    else:
                        st.error("会話の削除に失敗しました")
            
            # 日時とメッセージ数を小さく表示
            st.caption(f"🕒 {formatted_time} • 💬 {message_count}件")
    else:
        st.info("💬 まだ保存された会話がありません")

# チャット履歴の表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(sanitize_user_input(message["content"]))
        # 画像がある場合は表示
        if "image" in message:
            st.image(message["image"], caption="アップロードされた画像", width=300)

# ユーザー入力
if prompt := st.chat_input("メッセージを入力してください..."):
    # ファイルがアップロードされている場合の処理
    user_message_content = prompt
    user_message_data = {"role": "user", "content": user_message_content}
    
    if uploaded_file is not None:
        file_type = get_file_type(uploaded_file.name)
        
        if file_type == 'image':
            # 画像処理
            uploaded_file.seek(0)
            image_result = process_image(uploaded_file)
            if image_result:
                image, description = image_result
                user_message_content = f"{prompt}\n\n{description}"
                user_message_data["image"] = image
                user_message_data["content"] = user_message_content
        
        elif file_type == 'pdf':
            # PDF処理
            uploaded_file.seek(0)
            pdf_text = process_pdf(uploaded_file)
            if pdf_text:
                file_content = format_file_content_for_ai(file_type, pdf_text, uploaded_file.name)
                user_message_content = f"{prompt}\n\n{file_content}"
                user_message_data["content"] = user_message_content
    
    # ユーザーメッセージを履歴に追加
    st.session_state.messages.append(user_message_data)
    
    # データベースに保存（自動保存が有効な場合）
    if history_config.get("management", {}).get("auto_save", True):
        try:
            # セッションIDを確保
            if not st.session_state.current_session_id:
                new_session_id = history_manager.start_new_session(st.session_state.selected_model)
                st.session_state.current_session_id = new_session_id
            else:
                # 既存のセッションIDをhistory_managerに設定
                history_manager.set_current_session(st.session_state.current_session_id)
            
            image_data = user_message_data.get("image")
            history_manager.save_user_message(
                content=user_message_content,
                image=image_data,
                model_name=st.session_state.selected_model
            )
        except Exception as e:
            logger.error(f"ユーザーメッセージの保存に失敗: {e}")
    
    # ファイルがアップロードされていた場合はリセット
    if uploaded_file is not None:
        # ファイルアップロードをリセットするため、キーを変更してfile_uploaderを再生成
        st.session_state.file_uploader_key += 1
        st.rerun()
    
    # ユーザーメッセージを表示
    with st.chat_message("user"):
        st.markdown(sanitize_user_input(user_message_content))
        if "image" in user_message_data:
            st.image(user_message_data["image"], caption="アップロードされた画像", width=300)
    
    # AIの応答を生成
    with st.spinner("考え中..."):
        try:
            # 選択されたモデルを取得
            if not st.session_state.selected_model:
                show_api_key_error()
            elif not (model := create_model(st.session_state.selected_model)):
                st.error(f"モデル '{st.session_state.selected_model}' の初期化に失敗しました。")
            else:
                # LangChainメッセージ形式に変換
                langchain_messages = []
                model_config = ModelConfig.MODELS.get(st.session_state.selected_model, {})
                supports_vision = model_config.get("supports_vision", False)
                
                for msg in st.session_state.messages:
                    if msg["role"] == "user":
                        # 画像がある場合の処理
                        if "image" in msg and supports_vision:
                            try:
                                # 画像をbase64エンコード
                                image = msg["image"]
                                image_format = image.format or "PNG"
                                base64_image = encode_image_to_base64(image, image_format)
                                mime_type = get_image_mime_type(image_format)
                                
                                # マルチモーダルメッセージを作成（LangChain辞書形式）
                                content = [
                                    {"type": "text", "text": msg["content"]},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{mime_type};base64,{base64_image}"
                                        }
                                    }
                                ]
                                langchain_messages.append(HumanMessage(content=content))
                            except Exception as e:
                                logger.error(f"画像処理エラー: {e}")
                                # エラー時はテキストのみ
                                langchain_messages.append(HumanMessage(content=msg["content"]))
                        else:
                            # テキストのみ、または画像非対応モデル
                            langchain_messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        langchain_messages.append(AIMessage(content=msg["content"]))
                
                # システムメッセージを追加
                system_message = HumanMessage(content="あなたは親切で有用なAIアシスタントです。日本語で丁寧に回答してください。")
                langchain_messages.insert(0, system_message)
                
                # AIから応答を取得
                response = model.invoke(langchain_messages)
                ai_response = response.content
                
                # AIの応答を履歴に追加
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
                # データベースに保存（自動保存が有効な場合）
                if history_config.get("management", {}).get("auto_save", True):
                    try:
                        # セッションIDが設定されていることを確認
                        if st.session_state.current_session_id:
                            history_manager.set_current_session(st.session_state.current_session_id)
                        history_manager.save_assistant_message(ai_response)
                    except Exception as e:
                        logger.error(f"AIメッセージの保存に失敗: {e}")
                
                # ページを再読み込みして新しいメッセージを表示
                st.rerun()
            
        except Exception as e:
            error_message = str(e)
            st.error(f"エラーが発生しました: {error_message}")
            
            # エラーの種類に応じて適切なアドバイスを表示
            if "401" in error_message or "Unauthorized" in error_message:
                st.info("🔑 APIキーが無効です。正しいAPIキーを設定してください。")
            elif "403" in error_message or "Forbidden" in error_message:
                st.info("🚫 APIキーの権限が不足しています。APIキーの設定を確認してください。")
            elif "429" in error_message or "rate_limit" in error_message.lower():
                st.info("⏱️ レート制限に達しました。しばらく待ってから再試行してください。")
            elif "529" in error_message or "overloaded" in error_message.lower():
                st.info("⚡ サーバーが過負荷状態です。しばらく待ってから再試行してください。")
            elif "500" in error_message or "502" in error_message or "503" in error_message:
                st.info("🔧 サーバーで一時的な問題が発生しています。しばらく待ってから再試行してください。")
            else:
                st.info("💡 問題が解決しない場合は、APIキーの設定やネットワーク接続を確認してください。")
