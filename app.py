import streamlit as st
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from models import create_model, get_available_models, ModelConfig

# 環境変数の読み込み
load_dotenv()

# ページ設定
st.set_page_config(
    page_title="AIチャットボット",
    page_icon="🤖",
    layout="centered"
)

# タイトル
st.title("🤖 AIチャットボット")

# セッション状態の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_model" not in st.session_state:
    available_models = get_available_models()
    if available_models:
        st.session_state.selected_model = list(available_models.keys())[0]
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
                    st.error("利用可能なモデルがありません。APIキーを設定してください。")
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
    available_models = get_available_models()
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
        st.error("利用可能なモデルがありません。APIキーを設定してください。")
    
    # チャット履歴のクリア
    if st.button("チャット履歴をクリア"):
        st.session_state.messages = []
        st.rerun()
    
    # 使用方法の説明
    st.header("📖 使用方法")
    st.markdown("""
    1. `.env`ファイルを作成して各APIキーを設定
    2. サイドバーでAIモデルを選択
    3. チャット入力欄にメッセージを入力
    4. Enterを押してAIと会話開始
    """)
    
    st.header("🔧 セットアップ")
    
    # uvとpipの選択タブ
    tab1, tab2 = st.tabs(["uv (推奨)", "pip"])
    
    with tab1:
        st.code("""
# 依存関係のインストール
uv sync

# アプリの実行
uv run streamlit run app.py
        """)
    
    with tab2:
        st.code("""
# 依存関係のインストール
pip install -r requirements.txt

# アプリの実行
streamlit run app.py
        """)