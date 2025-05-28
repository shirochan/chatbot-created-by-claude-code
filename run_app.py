"""
アプリケーション実行スクリプト
プロジェクトルートから src.app を実行
"""
import sys
import os

# プロジェクトルートを確実にパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Streamlitアプリケーションの実行
if __name__ == "__main__":
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", "src/app.py"]
    sys.exit(stcli.main())