import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI

# 環境変数の読み込み
load_dotenv()

# OpenAI クライアントの初期化
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "あなたは親切で有用なAIアシスタントです。日本語で丁寧に回答してください。"},
                        *st.session_state.messages
                    ],
                    max_tokens=1000,
                    temperature=0.7
                )
                
                ai_response = response.choices[0].message.content
                st.markdown(ai_response)
                
                # AIの応答を履歴に追加
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")
                st.info("OpenAI APIキーが設定されているか確認してください。")

# サイドバーに設定オプション
with st.sidebar:
    st.header("⚙️ 設定")
    
    # チャット履歴のクリア
    if st.button("チャット履歴をクリア"):
        st.session_state.messages = []
        st.rerun()
    
    # 使用方法の説明
    st.header("📖 使用方法")
    st.markdown("""
    1. `.env`ファイルを作成してOpenAI APIキーを設定
    2. 下のチャット入力欄にメッセージを入力
    3. Enterを押してAIと会話開始
    """)
    
    st.header("🔧 セットアップ")
    st.code("""
    # 依存関係のインストール
    pip install -r requirements.txt
    
    # アプリの実行
    streamlit run app.py
    """)