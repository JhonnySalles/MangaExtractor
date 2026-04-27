import pytest
import numpy as np
from unittest.mock import patch, MagicMock, mock_open
from manga_extractor.modules.ocr import TextOcr

@pytest.fixture
def ocr_ja(operation_ja):
    return TextOcr(operation_ja)

@pytest.fixture
def ocr_pt(operation_pt):
    return TextOcr(operation_pt)

def test_ocr_initialization(ocr_ja, ocr_pt):
    assert ocr_ja.language == 'ja'
    assert "-l jpn" in ocr_ja.tesseractConfig
    assert ocr_pt.language == 'pt'
    assert "-l por" in ocr_pt.tesseractConfig

def test_ocr_languages(operation_pt):
    from manga_extractor.modules.ocr import TextOcr
    # Test English
    operation_pt.language = "en"
    ocr_en = TextOcr(operation_pt)
    assert "eng" in ocr_en.tesseractConfig
    
    # Test Japanese vertical
    operation_pt.language = "ja"
    operation_pt.verticalText = True
    ocr_ja_v = TextOcr(operation_pt)
    assert "jpn_vert" in ocr_ja_v.tesseractConfig

def test_filter_text_ja(ocr_ja):
    text = "Hello 日本語 123 !@#"
    filtered = ocr_ja.filterText(text)
    # ja filter removes English letters and numbers by default in characters regex
    assert "日本語" in filtered
    assert "Hello" not in filtered

def test_filter_text_pt(ocr_pt):
    text = "olá mundo 123 !@#"
    filtered = ocr_pt.filterText(text)
    assert "Olá mundo" in filtered # capitalizes

@patch('subprocess.Popen')
def test_get_text_window_ocr(mock_popen, ocr_pt):
    mock_p = mock_popen.return_value
    mock_p.wait.return_value = 0
    
    img = np.zeros((10, 10), dtype=np.uint8)
    
    with patch('builtins.open', mock_open(read_data="Ocr Result")):
        with patch('os.path.exists', return_value=True), \
             patch('os.remove'), \
             patch('cv2.imwrite'):
            res = ocr_pt.getTextWindowOcr(img)
            assert res == "Ocr result"

@patch('subprocess.Popen')
@patch('os.path.exists', return_value=True)
def test_check_window_ocr(mock_exists, mock_popen, ocr_pt):
    mock_p = mock_popen.return_value
    mock_p.wait.return_value = 0
    
    with patch('builtins.open', mock_open(read_data="True")):
        assert ocr_pt.checkWindowOcr() is True

@patch('pytesseract.image_to_string')
@patch('PIL.Image.open')
@patch('cv2.imwrite')
def test_get_text_tesseract_ocr(mock_write, mock_img_open, mock_tess, ocr_pt):
    mock_tess.return_value = "Tesseract Result"
    img = np.zeros((10, 10), dtype=np.uint8)
    
    res = ocr_pt.getTextTesseractOcr(img, "folder/")
    assert res == "Tesseract result"
    mock_tess.assert_called_once()

@patch('cv2.imread')
@patch('cv2.imwrite')
@patch('os.path.exists', return_value=True)
def test_get_text_from_img(mock_exists, mock_write, mock_read, ocr_pt):
    # Mock imread to return 100x100 image
    mock_read.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # rectP: [(x1, y1, x2, y2)], rect: [...]
    rect_list = ([(10, 10, 50, 50)], [])
    
    with patch.object(ocr_pt, 'getText', return_value="Found Text"):
        texts = ocr_pt.getTextFromImg("test.jpg", rect_list, "text/", "furi/")
        assert len(texts) == 1
        assert texts[0].text == "Found Text"

@patch('cv2.imread')
@patch('cv2.imwrite')
@patch('os.path.exists', return_value=True)
def test_get_text_from_img_furigana_fallback(mock_exists, mock_write, mock_read, ocr_ja):
    ocr_ja.operation.furigana = True
    
    # Mock imread to return 100x100 image for each call
    mock_read.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
    
    rect_list = ([(10, 10, 50, 50)], [])
    
    with patch.object(ocr_ja, 'getText') as mock_get_text:
        # First call returns empty, second call (fallback) returns text
        mock_get_text.side_effect = ["", "Fallback Text"]
        
        texts = ocr_ja.getTextFromImg("test.jpg", rect_list, "text/", "furi/")
        assert len(texts) == 1
        assert texts[0].text == "Fallback Text"
        assert mock_get_text.call_count == 2
