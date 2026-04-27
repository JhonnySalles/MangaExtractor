import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from manga_extractor.modules.furigana import RemoveFurigana

@pytest.fixture
def furigana_tool(operation_ja):
    return RemoveFurigana(operation_ja)

def test_cc_center(furigana_tool):
    # (slice(y1, y2), slice(x1, x2))
    comp = (slice(10, 20), slice(30, 50))
    # y_center = 15, x_center = 40
    assert furigana_tool.cc_center(comp) == (40, 15)

def test_is_in_component(furigana_tool):
    comp = (slice(10, 20), slice(30, 50))
    assert furigana_tool.is_in_component(15, 40, comp) is True
    assert furigana_tool.is_in_component(5, 40, comp) is False

def test_cc_width(furigana_tool):
    comp = (slice(10, 20), slice(30, 50))
    assert furigana_tool.cc_width(comp) == 20

@patch('manga_extractor.modules.cleaning.binarize')
@patch('manga_extractor.utils.helpers.average_size')
@patch('manga_extractor.utils.helpers.get_connected_components')
def test_estimate_furigana(mock_get_cc, mock_avg, mock_bin, furigana_tool):
    img = np.zeros((100, 100), dtype=np.uint8)
    segmentation = np.zeros((100, 100), dtype=np.uint8)
    
    mock_bin.return_value = img
    mock_avg.return_value = 10
    # Two boxes, one is a "furigana" (thin) to the left of another
    # Box 1: (y:10-20, x:35-40) - width 5
    # Box 2: (y:10-20, x:45-60) - width 15
    boxes = [
        (slice(10, 20), slice(45, 60)), # Main text
        (slice(10, 20), slice(35, 40))  # Furigana
    ]
    mock_get_cc.return_value = boxes
    
    res = furigana_tool.estimate_furigana(img, segmentation)
    assert res.shape == (100, 100)

@patch('cv2.imwrite')
def test_remove_furigana(mock_write, furigana_tool):
    img_gray = np.zeros((100, 100), dtype=np.uint8)
    img_clean = np.zeros((100, 100), dtype=np.uint8)
    img_segment = np.zeros((100, 100), dtype=np.uint8)
    
    with patch.object(furigana_tool, 'estimate_furigana') as mock_est:
        mock_est.return_value = np.zeros((100, 100), dtype=np.uint8)
        furigana_tool.removeFurigana("test.jpg", img_gray, img_clean, img_segment, "text/", "furi/")
        assert mock_write.call_count == 2
