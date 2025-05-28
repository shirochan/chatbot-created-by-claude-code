# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# uvのインストール
RUN pip install uv

# 依存関係ファイルのコピーと環境構築
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY tests/ ./tests/
COPY config.yaml ./

# 依存関係のインストール（開発用依存関係も含む）
RUN uv sync

# Production stage
FROM python:3.11-slim as production

WORKDIR /app

# システムパッケージのアップデート（curlのみ、ヘルスチェック用）
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uvのインストール
RUN pip install uv

# ビルドステージから必要なファイルのみコピー
COPY --from=builder /app/src /app/src
COPY --from=builder /app/config.yaml /app/config.yaml
COPY --from=builder /app/pyproject.toml /app/pyproject.toml
COPY --from=builder /app/uv.lock /app/uv.lock
COPY .env.example ./

# プロダクション用依存関係のみインストール
RUN uv sync --no-dev

# 環境変数設定
ENV PATH="/app/.venv/bin:$PATH"

# ポート8501を公開
EXPOSE 8501

# ヘルスチェック
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# アプリケーションの起動
CMD ["python", "-m", "streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]