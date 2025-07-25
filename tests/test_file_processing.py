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
    get_image_mime_type,
    validate_file_content,
    sanitize_user_input
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
    
    @patch('src.utils.file_processing.validate_file_content')
    def test_file_type_with_validation_success(self, mock_validate):
        """ファイル内容検証成功のテスト"""
        mock_file = Mock()
        mock_validate.return_value = True
        
        result = get_file_type("test.jpg", mock_file)
        
        assert result == "image"
        mock_validate.assert_called_once_with(mock_file)
    
    @patch('src.utils.file_processing.validate_file_content')
    def test_file_type_with_validation_failure(self, mock_validate):
        """ファイル内容検証失敗のテスト"""
        mock_file = Mock()
        mock_validate.return_value = False
        
        result = get_file_type("test.jpg", mock_file)
        
        assert result == "unknown"
        mock_validate.assert_called_once_with(mock_file)
    
    def test_file_type_without_validation(self):
        """ファイル内容検証なしのテスト（後方互換性）"""
        result = get_file_type("test.jpg")
        assert result == "image"

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

class TestFileValidation:
    """ファイル内容検証のテスト"""
    
    @patch('magic.from_buffer')
    def test_validate_file_content_success_png(self, mock_magic):
        """PNG画像ファイルの検証成功テスト"""
        mock_file = Mock()
        mock_file.seek = Mock()
        mock_file.read.return_value = b'fake_png_data'
        mock_magic.return_value = 'image/png'
        
        result = validate_file_content(mock_file)
        
        assert result is True
        mock_file.seek.assert_called_with(0)
        mock_file.read.assert_called_once_with(2048)
        mock_magic.assert_called_once_with(b'fake_png_data', mime=True)
    
    @patch('magic.from_buffer')
    def test_validate_file_content_success_pdf(self, mock_magic):
        """PDFファイルの検証成功テスト"""
        mock_file = Mock()
        mock_file.seek = Mock()
        mock_file.read.return_value = b'fake_pdf_data'
        mock_magic.return_value = 'application/pdf'
        
        result = validate_file_content(mock_file)
        
        assert result is True
        mock_file.seek.assert_called_with(0)
        mock_magic.assert_called_once_with(b'fake_pdf_data', mime=True)
    
    @patch('magic.from_buffer')
    def test_validate_file_content_failure_malicious(self, mock_magic):
        """悪意あるファイルの検証失敗テスト"""
        mock_file = Mock()
        mock_file.seek = Mock()
        mock_file.read.return_value = b'fake_executable_data'
        mock_magic.return_value = 'application/x-executable'
        
        result = validate_file_content(mock_file)
        
        assert result is False
        mock_file.seek.assert_called_with(0)
        mock_magic.assert_called_once_with(b'fake_executable_data', mime=True)
    
    @patch('magic.from_buffer')
    def test_validate_file_content_failure_text(self, mock_magic):
        """テキストファイルの検証失敗テスト"""
        mock_file = Mock()
        mock_file.seek = Mock()
        mock_file.read.return_value = b'plain text content'
        mock_magic.return_value = 'text/plain'
        
        result = validate_file_content(mock_file)
        
        assert result is False
        mock_file.seek.assert_called_with(0)
        mock_magic.assert_called_once_with(b'plain text content', mime=True)
    
    @patch('magic.from_buffer')
    def test_validate_file_content_exception_handling(self, mock_magic):
        """例外発生時のテスト"""
        mock_file = Mock()
        mock_file.seek = Mock()
        mock_file.read.side_effect = Exception("File read error")
        
        result = validate_file_content(mock_file)
        
        assert result is False
        mock_file.seek.assert_called_with(0)
    
    @patch('magic.from_buffer')
    def test_validate_file_content_magic_exception(self, mock_magic):
        """magic処理例外のテスト"""
        mock_file = Mock()
        mock_file.seek = Mock()
        mock_file.read.return_value = b'fake_data'
        mock_magic.side_effect = Exception("Magic processing error")
        
        result = validate_file_content(mock_file)
        
        assert result is False
        mock_file.seek.assert_called_with(0)
    
    @patch('magic.from_buffer')
    def test_validate_file_content_file_pointer_reset(self, mock_magic):
        """ファイルポインタリセット確認テスト"""
        mock_file = Mock()
        mock_file.seek = Mock()
        mock_file.read.return_value = b'fake_data'
        mock_magic.return_value = 'image/jpeg'
        
        validate_file_content(mock_file)
        
        # ファイルポインタが2回先頭に戻されることを確認
        assert mock_file.seek.call_count == 2
        from unittest.mock import call
        mock_file.seek.assert_has_calls([call(0), call(0)])
    
    @patch('magic.from_buffer')
    def test_validate_all_supported_mime_types(self, mock_magic):
        """サポートされる全MIMEタイプのテスト"""
        mock_file = Mock()
        mock_file.seek = Mock()
        mock_file.read.return_value = b'fake_data'
        
        supported_types = [
            'image/png', 'image/jpeg', 'image/gif', 
            'image/bmp', 'image/webp', 'application/pdf'
        ]
        
        for mime_type in supported_types:
            mock_magic.return_value = mime_type
            result = validate_file_content(mock_file)
            assert result is True, f"Failed for MIME type: {mime_type}"

class TestSanitizeUserInput:
    """ユーザー入力サニタイズのテスト"""
    
    def test_sanitize_basic_html_escape(self):
        """基本的なHTMLエスケープのテスト"""
        input_text = "<script>alert('XSS')</script>"
        result = sanitize_user_input(input_text)
        
        # スクリプトタグがエスケープされていることを確認
        assert "<script>" not in result
        assert "alert('XSS')" not in result
        assert "&lt;script&gt;" in result or "script" not in result
    
    def test_sanitize_img_tag_attack(self):
        """imgタグを使ったXSS攻撃のテスト"""
        input_text = "<img src=x onerror=alert('XSS')>"
        result = sanitize_user_input(input_text)
        
        # imgタグとonerrorが除去されていることを確認
        assert "<img" not in result
        assert "onerror" not in result
        assert "alert('XSS')" not in result
    
    def test_sanitize_javascript_protocol(self):
        """JavaScriptプロトコルを使った攻撃のテスト"""
        input_text = "[Click me](javascript:alert('XSS'))"
        result = sanitize_user_input(input_text)
        
        # JavaScriptプロトコルが除去されていることを確認
        assert "javascript:" not in result
        assert "alert('XSS')" not in result
    
    def test_sanitize_allowed_tags(self):
        """許可されたタグの処理テスト"""
        input_text = "<b>Bold text</b> <em>Emphasized text</em> <code>Code text</code>"
        result = sanitize_user_input(input_text)
        
        # 許可されたタグが保持されていることを確認
        assert "<b>" in result or "Bold text" in result
        assert "<em>" in result or "Emphasized text" in result
        assert "<code>" in result or "Code text" in result
    
    def test_sanitize_mixed_content(self):
        """許可されたタグと危険なタグの混在テスト"""
        input_text = "<b>Safe bold</b> <script>alert('XSS')</script> <em>Safe emphasis</em>"
        result = sanitize_user_input(input_text)
        
        # 安全なタグは保持、危険なタグは除去
        assert ("Safe bold" in result)
        assert ("Safe emphasis" in result)
        assert "<script>" not in result
        assert "alert('XSS')" not in result
    
    def test_sanitize_empty_content(self):
        """空の内容のテスト"""
        assert sanitize_user_input("") == ""
        assert sanitize_user_input(None) is None
    
    def test_sanitize_normal_text(self):
        """通常のテキストの処理テスト"""
        input_text = "This is normal text without any HTML tags."
        result = sanitize_user_input(input_text)
        
        # 通常のテキストはそのまま保持
        assert result == input_text
    
    def test_sanitize_complex_xss_attack(self):
        """複雑なXSS攻撃のテスト"""
        input_text = """
        <div onclick="alert('XSS')">Click me</div>
        <svg onload="alert('XSS')">
        <iframe src="javascript:alert('XSS')"></iframe>
        <a href="javascript:alert('XSS')">Link</a>
        """
        result = sanitize_user_input(input_text)
        
        # 全ての危険な要素が除去されていることを確認
        assert "onclick" not in result
        assert "onload" not in result
        assert "javascript:" not in result
        assert "alert('XSS')" not in result
        assert "<svg" not in result
        assert "<iframe" not in result
    
    def test_sanitize_error_handling(self):
        """エラーハンドリングのテスト"""
        # 非常に長い文字列や特殊文字でエラーが発生しないことを確認
        long_text = "A" * 10000 + "<script>alert('XSS')</script>"
        result = sanitize_user_input(long_text)
        
        # エラーが発生せず、危険なコンテンツが除去されていることを確認
        assert result is not None
        assert "<script>" not in result
        assert "alert('XSS')" not in result
    
    @patch('src.utils.file_processing.bleach.clean')
    def test_sanitize_bleach_exception(self, mock_clean):
        """bleach処理でエラーが発生した場合のフォールバックテスト"""
        mock_clean.side_effect = Exception("Bleach error")
        
        input_text = "<script>alert('XSS')</script>"
        result = sanitize_user_input(input_text)
        
        # エラーが発生してもHTMLエスケープは実行される
        assert result is not None
        assert "&lt;script&gt;" in result
        assert "alert(&#x27;XSS&#x27;)" in result  # エスケープされた状態で含まれる