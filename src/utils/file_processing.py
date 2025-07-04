"""
ファイル処理ユーティリティ
画像およびPDFファイルの処理機能を提供
"""
import io
import base64
import logging
from typing import Optional, Tuple, Union
from PIL import Image
import PyPDF2
import pdfplumber
import magic

logger = logging.getLogger(__name__)

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
        uploaded_file: Streamlitのアップロードファイルオブジェクト (オプション)

    Returns:
        str: ファイル種類 ('image', 'pdf', 'unknown')
    """
    if not file_name:
        return 'unknown'

    # コンテンツベースの検証 (優先)
    if uploaded_file:
        try:
            mime_type = validate_file_content(uploaded_file)
            if mime_type:
                if mime_type.startswith('image/'):
                    return 'image'
                elif mime_type == 'application/pdf':
                    return 'pdf'
        except Exception as e:
            logger.warning(f"ファイル内容の検証中にエラーが発生: {e}")

    # 拡張子ベースのフォールバック
    extension = file_name.lower().split('.')[-1]
    if extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
        return 'image'
    elif extension == 'pdf':
        return 'pdf'
    else:
        return 'unknown'


def validate_file_content(uploaded_file) -> Optional[str]:
    """
    マジックバイトを使用してファイル内容を検証

    Args:
        uploaded_file: Streamlitのアップロードファイルオブジェクト

    Returns:
        str: 検証されたMIMEタイプ、または無効な場合はNone
    """
    try:
        # ファイルの先頭2048バイトを読み込む
        uploaded_file.seek(0)
        file_content = uploaded_file.read(2048)
        uploaded_file.seek(0)  # ポインタを元に戻す

        # MIMEタイプを判定
        mime_type = magic.from_buffer(file_content, mime=True)
        logger.info(f"ファイルを検証: {uploaded_file.name}, MIMEタイプ: {mime_type}")

        # 許可されたMIMEタイプのリスト
        # config.yamlから取得するのが望ましいが、一旦ハードコード
        allowed_mime_types = {
            'image/png', 'image/jpeg', 'image/gif',
            'image/bmp', 'image/webp', 'application/pdf'
        }

        if mime_type in allowed_mime_types:
            return mime_type
        else:
            logger.warning(f"許可されていないMIMEタイプ: {mime_type} ({uploaded_file.name})")
            return None
    except Exception as e:
        logger.error(f"ファイル内容の検証エラー: {e}")
        return None


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