"""
ファイル処理機能のテスト
"""
import pytest
import io
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from src.utils.file_processing import (
    process_image, 
    process_pdf,
    get_file_type,
    format_file_content_for_ai,
    process_pdf_with_pypdf2,
    process_pdf_with_pdfplumber,
    encode_image_to_base64,
    get_image_mime_type
)

class TestGetFileType:
    """ファイル種類判定のテスト"""
    
    def test_image_files(self):
        """画像ファイルの判定テスト"""
        assert get_file_type("test.jpg") == "image"
        assert get_file_type("test.jpeg") == "image"
        assert get_file_type("test.png") == "image"
        assert get_file_type("test.gif") == "image"
        assert get_file_type("test.bmp") == "image"
        assert get_file_type("test.webp") == "image"
        
    def test_pdf_files(self):
        """PDFファイルの判定テスト"""
        assert get_file_type("test.pdf") == "pdf"
        assert get_file_type("document.PDF") == "pdf"  # 大文字小文字混在
        
    def test_unknown_files(self):
        """未対応ファイルの判定テスト"""
        assert get_file_type("test.txt") == "unknown"
        assert get_file_type("test.docx") == "unknown"
        assert get_file_type("test.svg") == "unknown"  # SVGは未対応
        assert get_file_type("") == "unknown"
        assert get_file_type(None) == "unknown"

class TestProcessImage:
    """画像処理のテスト"""
    
    def test_process_image_success(self):
        """画像処理成功のテスト"""
        # モックファイルを作成
        mock_file = Mock()
        mock_file.name = "test.jpg"
        
        # PIL Imageオブジェクトをモック
        mock_image = Mock(spec=Image.Image)
        mock_image.size = (800, 600)
        mock_image.format = "JPEG"
        mock_image.mode = "RGB"
        
        with patch('PIL.Image.open', return_value=mock_image) as mock_open:
            result = process_image(mock_file)
            
            assert result is not None
            image, description = result
            assert image == mock_image
            assert "test.jpg" in description
            assert "800 x 600" in description
            assert "JPEG" in description
            assert "RGB" in description
            mock_open.assert_called_once_with(mock_file)
    
    def test_process_image_failure(self):
        """画像処理失敗のテスト"""
        mock_file = Mock()
        mock_file.name = "invalid.jpg"
        
        with patch('PIL.Image.open', side_effect=Exception("Invalid image")) as mock_open:
            result = process_image(mock_file)
            
            assert result is None
            mock_open.assert_called_once_with(mock_file)

class TestProcessPdf:
    """PDF処理のテスト"""
    
    @patch('src.utils.file_processing.process_pdf_with_pdfplumber')
    def test_process_pdf_pdfplumber_success(self, mock_pdfplumber):
        """pdfplumberでのPDF処理成功テスト"""
        mock_file = Mock()
        mock_pdfplumber.return_value = "PDF content from pdfplumber"
        
        result = process_pdf(mock_file)
        
        assert result == "PDF content from pdfplumber"
        mock_pdfplumber.assert_called_once_with(mock_file)
    
    @patch('src.utils.file_processing.process_pdf_with_pypdf2')
    @patch('src.utils.file_processing.process_pdf_with_pdfplumber')
    def test_process_pdf_fallback_to_pypdf2(self, mock_pdfplumber, mock_pypdf2):
        """pdfplumber失敗時のPyPDF2フォールバックテスト"""
        mock_file = Mock()
        mock_pdfplumber.return_value = None
        mock_pypdf2.return_value = "PDF content from PyPDF2"
        
        result = process_pdf(mock_file)
        
        assert result == "PDF content from PyPDF2"
        mock_pdfplumber.assert_called_once_with(mock_file)
        mock_pypdf2.assert_called_once_with(mock_file)
    
    @patch('src.utils.file_processing.process_pdf_with_pypdf2')
    @patch('src.utils.file_processing.process_pdf_with_pdfplumber')
    def test_process_pdf_both_fail(self, mock_pdfplumber, mock_pypdf2):
        """両方の処理が失敗した場合のテスト"""
        mock_file = Mock()
        mock_pdfplumber.return_value = None
        mock_pypdf2.return_value = None
        
        result = process_pdf(mock_file)
        
        assert result is None
        mock_pdfplumber.assert_called_once_with(mock_file)
        mock_pypdf2.assert_called_once_with(mock_file)
    
    @patch('src.utils.config.get_file_upload_config')
    @patch('src.utils.file_processing.process_pdf_with_pypdf2')
    @patch('src.utils.file_processing.process_pdf_with_pdfplumber')
    def test_process_pdf_custom_engine_order(self, mock_pdfplumber, mock_pypdf2, mock_config):
        """設定ファイルでカスタムエンジン順序を指定した場合のテスト"""
        mock_file = Mock()
        mock_pdfplumber.return_value = "pdfplumber result"
        mock_pypdf2.return_value = "pypdf2 result"
        
        # PyPDF2を先に試すよう設定
        mock_config.return_value = {
            "pdf_processing": {
                "engines": ["pypdf2", "pdfplumber"]
            }
        }
        
        result = process_pdf(mock_file)
        
        assert result == "pypdf2 result"
        mock_pypdf2.assert_called_once_with(mock_file)
        # pdfplumberは呼ばれない（PyPDF2で成功したため）
        mock_pdfplumber.assert_not_called()
    
    @patch('src.utils.config.get_file_upload_config')
    @patch('src.utils.file_processing.process_pdf_with_pypdf2')
    @patch('src.utils.file_processing.process_pdf_with_pdfplumber')
    def test_process_pdf_fallback_on_config_error(self, mock_pdfplumber, mock_pypdf2, mock_config):
        """設定読み込みエラー時のフォールバック動作テスト"""
        mock_file = Mock()
        mock_pdfplumber.return_value = "pdfplumber result"
        mock_config.side_effect = ImportError("config error")
        
        result = process_pdf(mock_file)
        
        assert result == "pdfplumber result"
        mock_pdfplumber.assert_called_once_with(mock_file)

class TestProcessPdfWithPyPdf2:
    """PyPDF2でのPDF処理テスト"""
    
    @patch('PyPDF2.PdfReader')
    def test_pypdf2_success(self, mock_pdf_reader):
        """PyPDF2での処理成功テスト"""
        mock_file = Mock()
        mock_file.seek = Mock()
        
        # モックページを作成
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 content"
        
        # モックPDFリーダーを設定
        mock_reader_instance = Mock()
        mock_reader_instance.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader_instance
        
        result = process_pdf_with_pypdf2(mock_file)
        
        assert result is not None
        assert "Page 1 content" in result
        assert "Page 2 content" in result
        assert "--- ページ 1 ---" in result
        assert "--- ページ 2 ---" in result
        mock_file.seek.assert_called_once_with(0)
    
    @patch('PyPDF2.PdfReader')
    def test_pypdf2_failure(self, mock_pdf_reader):
        """PyPDF2での処理失敗テスト"""
        mock_file = Mock()
        mock_file.seek = Mock()
        mock_pdf_reader.side_effect = Exception("PDF reading error")
        
        result = process_pdf_with_pypdf2(mock_file)
        
        assert result is None
        mock_file.seek.assert_called_once_with(0)

class TestProcessPdfWithPdfplumber:
    """pdfplumberでのPDF処理テスト"""
    
    @patch('pdfplumber.open')
    def test_pdfplumber_success(self, mock_pdfplumber_open):
        """pdfplumberでの処理成功テスト"""
        mock_file = Mock()
        mock_file.seek = Mock()
        
        # モックページを作成
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 content"
        
        # モックPDFオブジェクトを作成
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=None)
        
        mock_pdfplumber_open.return_value = mock_pdf
        
        result = process_pdf_with_pdfplumber(mock_file)
        
        assert result is not None
        assert "Page 1 content" in result
        assert "Page 2 content" in result
        assert "--- ページ 1 ---" in result
        assert "--- ページ 2 ---" in result
        mock_file.seek.assert_called_once_with(0)
    
    @patch('pdfplumber.open')
    def test_pdfplumber_failure(self, mock_pdfplumber_open):
        """pdfplumberでの処理失敗テスト"""
        mock_file = Mock()
        mock_file.seek = Mock()
        mock_pdfplumber_open.side_effect = Exception("PDF reading error")
        
        result = process_pdf_with_pdfplumber(mock_file)
        
        assert result is None
        mock_file.seek.assert_called_once_with(0)

class TestFormatFileContentForAi:
    """AIモデル向けフォーマット機能のテスト"""
    
    def test_format_pdf_content(self):
        """PDF内容のフォーマットテスト"""
        result = format_file_content_for_ai("pdf", "PDF text content", "document.pdf")
        
        assert "PDFファイル「document.pdf」の内容:" in result
        assert "PDF text content" in result
    
    def test_format_image_content(self):
        """画像内容のフォーマットテスト"""
        mock_image = Mock(spec=Image.Image)
        result = format_file_content_for_ai("image", mock_image, "photo.jpg")
        
        assert "画像ファイル「photo.jpg」がアップロードされました" in result
        assert "この画像について質問してください" in result
    
    def test_format_unknown_content(self):
        """未知のファイル形式のフォーマットテスト"""
        result = format_file_content_for_ai("unknown", "some content", "file.xyz")
        
        assert "不明なファイル形式: file.xyz" in result

class TestEdgeCases:
    """エッジケースのテスト"""
    
    def test_empty_pdf_pages(self):
        """空のPDFページの処理テスト"""
        mock_file = Mock()
        mock_file.seek = Mock()
        
        with patch('pdfplumber.open') as mock_open:
            mock_page = Mock()
            mock_page.extract_text.return_value = ""  # 空のテキスト
            
            mock_pdf = Mock()
            mock_pdf.pages = [mock_page]
            mock_pdf.__enter__ = Mock(return_value=mock_pdf)
            mock_pdf.__exit__ = Mock(return_value=None)
            
            mock_open.return_value = mock_pdf
            
            result = process_pdf_with_pdfplumber(mock_file)
            assert result is None
    
    def test_image_with_special_characters_in_filename(self):
        """特殊文字を含むファイル名の画像処理テスト"""
        mock_file = Mock()
        mock_file.name = "テスト画像 (1).jpg"
        
        mock_image = Mock(spec=Image.Image)
        mock_image.size = (100, 100)
        mock_image.format = "JPEG"
        mock_image.mode = "RGB"
        
        with patch('PIL.Image.open', return_value=mock_image):
            result = process_image(mock_file)
            
            assert result is not None
            image, description = result
            assert "テスト画像 (1).jpg" in description

class TestBase64Encoding:
    """base64エンコード機能のテスト"""
    
    @patch('io.BytesIO')
    def test_encode_image_to_base64(self, mock_bytesio):
        """画像のbase64エンコードテスト"""
        # モックの設定
        mock_buffer = Mock()
        mock_buffer.read.return_value = b'fake_image_data'
        mock_bytesio.return_value = mock_buffer
        
        mock_image = Mock(spec=Image.Image)
        mock_image.save = Mock()
        
        result = encode_image_to_base64(mock_image, "PNG")
        
        # base64エンコードされた結果を確認
        expected = "ZmFrZV9pbWFnZV9kYXRh"  # b'fake_image_data'のbase64
        assert result == expected
        mock_image.save.assert_called_once_with(mock_buffer, format="PNG")
        mock_buffer.seek.assert_called_once_with(0)
    
    def test_get_image_mime_type(self):
        """MIMEタイプ取得のテスト"""
        assert get_image_mime_type("PNG") == "image/png"
        assert get_image_mime_type("JPEG") == "image/jpeg"
        assert get_image_mime_type("JPG") == "image/jpeg"
        assert get_image_mime_type("GIF") == "image/gif"
        assert get_image_mime_type("BMP") == "image/bmp"
        assert get_image_mime_type("WEBP") == "image/webp"
        assert get_image_mime_type("UNKNOWN") == "image/png"  # デフォルト値

class TestMultimodalSupport:
    """マルチモーダル対応のテスト"""
    
    def test_vision_model_configuration(self):
        """ビジョン対応モデルの設定テスト"""
        from src.models.config import ModelConfig
        
        # GPT-4oがビジョン対応として設定されていることを確認
        gpt4o_config = ModelConfig.MODELS.get("GPT-4o", {})
        assert gpt4o_config.get("supports_vision") is True
        
        # Claude Sonnet 4がビジョン対応として設定されていることを確認
        claude_config = ModelConfig.MODELS.get("Claude Sonnet 4", {})
        assert claude_config.get("supports_vision") is True
        
        # GPT-4.1が非対応として設定されていることを確認
        gpt41_config = ModelConfig.MODELS.get("GPT-4.1", {})
        assert gpt41_config.get("supports_vision") is False