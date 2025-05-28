# AIチャットボット

LangChainを使用したマルチプロバイダー対応のAIチャットボットアプリケーション

## 🚀 機能

- **マルチAIプロバイダー対応**: OpenAI、Anthropic、Google Geminiを統一インターフェースで利用
- **リアルタイム会話**: AIとのインタラクティブなチャット
- **モデル選択**: 5つのAIモデルから選択可能
  - GPT-4o (OpenAI)
  - GPT-4.1 (OpenAI) 
  - Claude Sonnet 4 (Anthropic)
  - Claude Opus 4 (Anthropic)
  - Gemini 2.5 Flash (Google)
- **チャット履歴**: セッション内でのメッセージ履歴管理
- **レスポンシブUI**: Streamlitベースのクリーンなインターフェース
- **包括的テスト**: 29のテストケースによる品質保証

## 📦 プロジェクト構造

```
chatbot-created-by-claude-code/
├── src/                        # ソースコード
│   ├── __init__.py             # パッケージ初期化
│   ├── __main__.py             # モジュール実行エントリーポイント
│   ├── app.py                  # メインアプリケーション
│   ├── models/                 # AIモデル管理
│   │   ├── __init__.py         # パッケージ初期化
│   │   ├── config.py           # モデル設定
│   │   └── factory.py          # モデル作成機能
│   └── utils/                  # ユーティリティ
│       ├── __init__.py         # パッケージ初期化
│       ├── config.py           # 設定管理
│       └── logging.py          # ログ設定
├── tests/                      # テストスイート
│   ├── __init__.py             # パッケージ初期化
│   ├── conftest.py             # テスト設定
│   ├── test_app.py            # アプリケーションテスト
│   └── test_models.py         # モデルテスト
├── config.yaml                # アプリケーション設定
├── Dockerfile                 # コンテナ設定
├── pytest.ini                 # テスト設定
├── pyproject.toml             # プロジェクト設定
├── uv.lock                    # 依存関係ロックファイル
└── .env.example               # 環境変数テンプレート
```

## 🛠️ セットアップ

### 前提条件

- Python 3.11+
- uv (モダンなPythonパッケージマネージャー)

### インストール手順

1. **リポジトリのクローン**:
```bash
git clone https://github.com/your-username/chatbot-created-by-claude-code.git
cd chatbot-created-by-claude-code
```

2. **依存関係のインストール**:
```bash
uv sync
```

3. **環境変数の設定**:
```bash
cp .env.example .env
```

`.env`ファイルを編集して必要なAPIキーを設定：
```bash
# 利用したいプロバイダーのAPIキーを設定
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here  
GOOGLE_API_KEY=your_google_api_key_here
```

## 🚀 実行方法

### ローカル実行

```bash
# 推奨: 直接実行
uv run streamlit run src/app.py

# または指定ポートで実行
uv run streamlit run src/app.py --server.port=8502
```

アプリケーションは http://localhost:8501 でアクセスできます。

### Docker実行

```bash
# プロダクション用イメージのビルド
docker build -t chatbot-app .

# コンテナの実行
docker run -p 8501:8501 --env-file .env chatbot-app

# 開発用（テスト含む）イメージのビルド
docker build --target builder -t chatbot-app-dev .

# 開発用コンテナでテスト実行
docker run --rm chatbot-app-dev uv run pytest -v
```

## 🧪 テスト

```bash
# 全テストの実行
uv run pytest

# 詳細出力付きテスト
uv run pytest -v

# 詳細な失敗情報付きテスト
uv run pytest -vvs
```

## 📋 使用技術

### コア技術
- **Python 3.11**: プログラミング言語
- **Streamlit**: Webアプリケーションフレームワーク
- **LangChain**: AI/LLMアプリケーション開発フレームワーク

### AIプロバイダー
- **OpenAI**: GPT-4oおよびGPT-4.1
- **Anthropic**: Claude Sonnet 4およびClaude Opus 4
- **Google**: Gemini 2.5 Flash

### 開発・運用
- **uv**: モダンなPythonパッケージマネージャー
- **pytest**: テストフレームワーク
- **Docker**: コンテナ化
- **PyYAML**: YAML設定ファイル管理

## ⚙️ 設定

### config.yaml

アプリケーション設定は `config.yaml` で管理：

```yaml
# アプリケーション設定
app:
  title: "AIチャットボット"
  page_icon: "🤖"
  layout: "wide"                      # centered, wide
  initial_sidebar_state: "auto"      # auto, expanded, collapsed

# ログ設定
logging:
  level: "INFO"                       # DEBUG, INFO, WARNING, ERROR
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Streamlit設定
streamlit:
  server:
    port: 8501
    headless: true
  browser:
    gatherUsageStats: false

# チャット設定
chat:
  max_history: 100
  default_model: "GPT-4o"             # デフォルトで選択されるモデル
  show_model_description: true        # モデル説明の表示
```

### 環境変数

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `OPENAI_API_KEY` | OpenAI APIキー | OpenAIモデル使用時 |
| `ANTHROPIC_API_KEY` | Anthropic APIキー | Claudeモデル使用時 |
| `GOOGLE_API_KEY` | Google APIキー | Geminiモデル使用時 |

## 🤝 開発

### ブランチ戦略
- `main`: プロダクションブランチ
- `feature/*`: 新機能開発
- `fix/*`: バグ修正

### テスト
新機能追加時は対応するテストも追加してください：
```bash
# テスト追加例
tests/test_new_feature.py
```

### コード品質
プルリクエスト前に以下を実行：
```bash
uv run pytest -v  # 全テスト通過確認
```

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🔗 関連リンク

- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Google AI Gemini](https://ai.google.dev/)
- [LangChain Documentation](https://python.langchain.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)