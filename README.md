# AIチャットボット

StreamlitとOpenAI APIを使用したシンプルなチャットボットアプリケーション

## 機能

- リアルタイムでのAIとの会話
- チャット履歴の表示
- レスポンシブなUI
- 簡単なセットアップ

## セットアップ

### uvを使用する場合（推奨）

1. 依存関係のインストール:
```bash
uv sync
```

2. 環境変数の設定:
`.env`ファイルを作成し、OpenAI APIキーを設定
```bash
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

3. アプリケーションの実行:
```bash
uv run streamlit run app.py
```

### pipを使用する場合

1. 依存関係のインストール:
```bash
pip install -r requirements.txt
```

2. 環境変数の設定:
`.env`ファイルを作成し、OpenAI APIキーを設定
```
OPENAI_API_KEY=your_openai_api_key_here
```

3. アプリケーションの実行:
```bash
streamlit run app.py
```

## 使用技術

- Python 3.8+
- Streamlit
- OpenAI API
- python-dotenv

## ファイル構成

```
├── app.py              # メインアプリケーション
├── requirements.txt    # 依存関係
├── .env.example       # 環境変数のサンプル
└── README.md          # このファイル
```