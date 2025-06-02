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
    PDFファイルからテキストを抽出（フォールバック機能付き）
    
    Args:
        uploaded_file: Streamlitのアップロードファイルオブジェクト
        
    Returns:
        str: 抽出されたテキスト または None
    """
    # まずpdfplumberを試す（より高精度）
    result = process_pdf_with_pdfplumber(uploaded_file)
    
    if result is None:
        # フォールバックとしてPyPDF2を使用
        logger.info("pdfplumberが失敗したため、PyPDF2でリトライします")
        result = process_pdf_with_pypdf2(uploaded_file)
    
    return result

def get_file_type(file_name: str) -> str:
    """
    ファイル名から種類を判定
    
    Args:
        file_name: ファイル名
        
    Returns:
        str: ファイル種類 ('image', 'pdf', 'unknown')
    """
    if not file_name:
        return 'unknown'
    
    extension = file_name.lower().split('.')[-1]
    
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