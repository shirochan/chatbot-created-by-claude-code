"""
ファイル処理ユーティリティ
画像およびPDFファイルの処理機能を提供
"""
import io
import base64
import logging
import html
from typing import Optional, Tuple, Union
from PIL import Image
import PyPDF2
import pdfplumber
import magic
import bleach

logger = logging.getLogger(__name__)

def sanitize_user_input(content: str) -> str:
    """
    ユーザー入力を安全な表示用にサニタイズ
    XSS攻撃を防ぐためHTMLをエスケープし、安全なタグのみを許可
    
    Args:
        content: サニタイズするテキスト
        
    Returns:
        str: サニタイズされた安全なテキスト
    """
    if not content:
        return content
    
    try:
        # 危険なJavaScriptプロトコルを大文字小文字を区別せずに除去
        import re
        content = re.sub(r'javascript:', '', content, flags=re.IGNORECASE)
        content = re.sub(r'data:', '', content, flags=re.IGNORECASE)
        content = re.sub(r'vbscript:', '', content, flags=re.IGNORECASE)
        
        # 安全なタグのみを許可
        allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'code', 'pre', 'br', 'p']
        allowed_attributes = {}
        
        # bleachで危険なHTMLを除去（生のコンテンツに対して実行）
        clean_content = bleach.clean(
            content, 
            tags=allowed_tags, 
            attributes=allowed_attributes,
            strip=True
        )
        
        # HTMLエスケープ（許可されたタグ以外をエスケープ）
        escaped_content = html.escape(clean_content)
        
        logger.debug(f"ユーザー入力をサニタイズしました: {len(content)} -> {len(escaped_content)} 文字")
        return escaped_content
        
    except Exception as e:
        logger.error(f"サニタイズエラー: {e}")
        # エラーが発生した場合は基本的なHTMLエスケープのみ実行
        return html.escape(content)

def validate_file_content(uploaded_file) -> bool:
    """
    ファイル内容をマジックバイトで検証
    
    Args:
        uploaded_file: Streamlitのアップロードファイルオブジェクト
        
    Returns:
        bool: ファイル内容が安全かどうか
    """
    try:
        # ファイルポインタを先頭に戻す
        uploaded_file.seek(0)
        
        # 最初の2048バイトを読み込んで検証
        file_content = uploaded_file.read(2048)
        uploaded_file.seek(0)  # ポインタを先頭に戻す
        
        # マジックバイトからMIMEタイプを取得
        mime_type = magic.from_buffer(file_content, mime=True)
        
        # 許可されたMIMEタイプのセット
        allowed_mime_types = {
            'image/png', 'image/jpeg', 'image/gif', 
            'image/bmp', 'image/webp', 'application/pdf'
        }
        
        is_valid = mime_type in allowed_mime_types
        
        if is_valid:
            logger.info(f"ファイル検証成功: MIME={mime_type}")
        else:
            logger.warning(f"不正なファイル形式を検出: MIME={mime_type}")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"ファイル検証エラー: {e}")
        return False

def process_image(uploaded_file) -> Optional[Tuple[Image.Image, str]]:
    """
    アップロードされた画像ファイルを処理
    
    Args:
        uploaded_file: Streamlitのアップロードファイルオブジェクト
        
    Returns:
        tuple: (PIL Image オブジェクト, 画像の説明テキスト) または None
    """
    try:
        # 画像を開く
        image = Image.open(uploaded_file)
        
        # 画像情報を取得
        description = f"画像ファイル: {uploaded_file.name}\n"
        description += f"サイズ: {image.size[0]} x {image.size[1]} ピクセル\n"
        description += f"フォーマット: {image.format}\n"
        description += f"モード: {image.mode}"
        
        logger.info(f"画像ファイルを処理しました: {uploaded_file.name}")
        return image, description
        
    except Exception as e:
        logger.error(f"画像処理エラー: {e}")
        return None

def process_pdf_with_pypdf2(uploaded_file) -> Optional[str]:
    """
    PyPDF2を使用してPDFからテキストを抽出
    
    Args:
        uploaded_file: Streamlitのアップロードファイルオブジェクト
        
    Returns:
        str: 抽出されたテキスト または None
    """
    try:
        # ファイルポインタを先頭に戻す
        uploaded_file.seek(0)
        
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text_content = []
        
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if page_text.strip():
                    text_content.append(f"--- ページ {page_num + 1} ---\n{page_text}")
            except Exception as e:
                logger.warning(f"ページ {page_num + 1} の処理でエラー: {e}")
                continue
        
        if text_content:
            result = "\n\n".join(text_content)
            logger.info(f"PyPDF2でPDFを処理しました: {uploaded_file.name} ({len(pdf_reader.pages)}ページ)")
            return result
        else:
            logger.warning(f"PDFからテキストを抽出できませんでした: {uploaded_file.name}")
            return None
            
    except Exception as e:
        logger.error(f"PyPDF2でのPDF処理エラー: {e}")
        return None

def process_pdf_with_pdfplumber(uploaded_file) -> Optional[str]:
    """
    pdfplumberを使用してPDFからテキストを抽出
    
    Args:
        uploaded_file: Streamlitのアップロードファイルオブジェクト
        
    Returns:
        str: 抽出されたテキスト または None
    """
    try:
        # ファイルポインタを先頭に戻す
        uploaded_file.seek(0)
        
        with pdfplumber.open(uploaded_file) as pdf:
            text_content = []
            
            for page_num, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_content.append(f"--- ページ {page_num + 1} ---\n{page_text}")
                except Exception as e:
                    logger.warning(f"ページ {page_num + 1} の処理でエラー: {e}")
                    continue
            
            if text_content:
                result = "\n\n".join(text_content)
                logger.info(f"pdfplumberでPDFを処理しました: {uploaded_file.name} ({len(pdf.pages)}ページ)")
                return result
            else:
                logger.warning(f"PDFからテキストを抽出できませんでした: {uploaded_file.name}")
                return None
                
    except Exception as e:
        logger.error(f"pdfplumberでのPDF処理エラー: {e}")
        return None

def process_pdf(uploaded_file) -> Optional[str]:
    """
    PDFファイルからテキストを抽出（設定ファイルベースのエンジン優先順位）
    
    Args:
        uploaded_file: Streamlitのアップロードファイルオブジェクト
        
    Returns:
        str: 抽出されたテキスト または None
    """
    # 設定ファイルからエンジンの優先順位を取得
    try:
        from .config import get_file_upload_config
        file_config = get_file_upload_config()
        engines = file_config.get("pdf_processing", {}).get("engines", ["pdfplumber", "pypdf2"])
    except ImportError:
        # フォールバック: デフォルトの順序
        engines = ["pdfplumber", "pypdf2"]
    
    result = None
    
    # 設定された順序でエンジンを試行
    for engine in engines:
        if engine.lower() == "pdfplumber":
            result = process_pdf_with_pdfplumber(uploaded_file)
            if result is not None:
                break
            logger.info("pdfplumberが失敗、次のエンジンを試します")
        elif engine.lower() == "pypdf2":
            result = process_pdf_with_pypdf2(uploaded_file)
            if result is not None:
                break
            logger.info("PyPDF2が失敗、次のエンジンを試します")
        else:
            logger.warning(f"未知のPDFエンジン: {engine}")
    
    return result

def get_file_type(file_name: str, uploaded_file=None) -> str:
    """
    ファイル名と内容から種類を判定
    
    Args:
        file_name: ファイル名
        uploaded_file: アップロードファイルオブジェクト（内容検証用）
        
    Returns:
        str: ファイル種類 ('image', 'pdf', 'unknown')
    """
    if not file_name:
        return 'unknown'
    
    # 拡張子による基本判定
    extension = file_name.lower().split('.')[-1]
    
    # 拡張子が不正な場合は即座に拒否
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'pdf']
    if extension not in allowed_extensions:
        return 'unknown'
    
    # ファイル内容がある場合は内容検証を実施
    if uploaded_file is not None:
        if not validate_file_content(uploaded_file):
            logger.warning(f"ファイル内容検証失敗: {file_name}")
            return 'unknown'
    
    # 拡張子による分類
    if extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
        return 'image'
    elif extension == 'pdf':
        return 'pdf'
    else:
        return 'unknown'

def encode_image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """
    PIL Imageをbase64エンコード
    
    Args:
        image: PIL Imageオブジェクト
        format: 画像フォーマット (PNG, JPEG等)
        
    Returns:
        str: base64エンコードされた画像データ
    """
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode('utf-8')
    return encoded

def get_image_mime_type(format: str) -> str:
    """
    画像フォーマットからMIMEタイプを取得
    
    Args:
        format: 画像フォーマット
        
    Returns:
        str: MIMEタイプ
    """
    format_to_mime = {
        'PNG': 'image/png',
        'JPEG': 'image/jpeg',
        'JPG': 'image/jpeg',
        'GIF': 'image/gif',
        'BMP': 'image/bmp',
        'WEBP': 'image/webp'
    }
    return format_to_mime.get(format.upper(), 'image/png')

def format_file_content_for_ai(file_type: str, content: Union[str, Image.Image], file_name: str) -> str:
    """
    AIモデルに送信する形式でファイル内容をフォーマット
    
    Args:
        file_type: ファイルの種類
        content: ファイルの内容
        file_name: ファイル名
        
    Returns:
        str: フォーマットされたテキスト
    """
    if file_type == 'pdf':
        return f"PDFファイル「{file_name}」の内容:\n\n{content}"
    elif file_type == 'image':
        # 画像の場合は説明テキストのみ（実際の画像データは別途処理）
        return f"画像ファイル「{file_name}」がアップロードされました。この画像について質問してください。"
    else:
        return f"不明なファイル形式: {file_name}"