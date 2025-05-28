"""
パッケージのメインエントリーポイント
python -m src で実行可能
"""
import sys
import streamlit.web.cli as stcli

if __name__ == "__main__":
    import os
    # src/__main__.pyからsrc/app.pyを参照
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    sys.argv = ["streamlit", "run", app_path]
    sys.exit(stcli.main())