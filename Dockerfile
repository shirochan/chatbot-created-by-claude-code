# Python 3.11ベースイメージ
FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# システムパッケージのアップデート
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uvのインストール
RUN pip install uv

# プロジェクトファイルのコピー
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY config.yaml .env.example ./
COPY tests/ ./tests/

# 依存関係のインストール
RUN uv sync

# ポート8501を公開
EXPOSE 8501

# ヘルスチェック
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# アプリケーションの起動
CMD ["uv", "run", "streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]