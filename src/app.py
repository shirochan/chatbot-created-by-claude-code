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
from src.utils import setup_logging, get_app_config, get_logging_config, get_chat_config

# 環境変数の読み込み
load_dotenv()

# 設定の読み込み
app_config = get_app_config()
logging_config = get_logging_config()
chat_config = get_chat_config()

# ログ設定
logger = setup_logging(
    level=logging_config.get("level", "INFO"), 
    logger_name="chatbot"
)

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

# チャット履歴の表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザー入力
if prompt := st.chat_input("メッセージを入力してください..."):
    # ユーザーメッセージを履歴に追加
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # ユーザーメッセージを表示
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # AIの応答を生成
    with st.chat_message("assistant"):
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
                    for msg in st.session_state.messages:
                        if msg["role"] == "user":
                            langchain_messages.append(HumanMessage(content=msg["content"]))
                        elif msg["role"] == "assistant":
                            langchain_messages.append(AIMessage(content=msg["content"]))
                    
                    # システムメッセージを追加
                    system_message = HumanMessage(content="あなたは親切で有用なAIアシスタントです。日本語で丁寧に回答してください。")
                    langchain_messages.insert(0, system_message)
                    
                    # AIから応答を取得
                    response = model.invoke(langchain_messages)
                    ai_response = response.content
                    
                    st.markdown(ai_response)
                    
                    # AIの応答を履歴に追加
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")
                st.info("APIキーが正しく設定されているか確認してください。")

# サイドバーに設定オプション
with st.sidebar:
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
            st.info(f"📝 {available_models[selected_model]['description']}")
    else:
        show_api_key_error()
    
    # チャット履歴のクリア
    if st.button("チャット履歴をクリア"):
        st.session_state.messages = []
        st.rerun()
