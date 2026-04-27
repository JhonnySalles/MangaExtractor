import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from manga_extractor.modules.detection import TextDetection

def test_text_detection_initialization():
    td = TextDetection(0.05)
    assert td.contourSize == 0.05

@patch('cv2.Sobel')
@patch('cv2.threshold')
@patch('cv2.getStructuringElement')
@patch('cv2.morphologyEx')
@patch('cv2.findContours')
@patch('cv2.boundingRect')
def test_text_detect_logic(mock_rect, mock_find, mock_morph, mock_struct, mock_thresh, mock_sobel):
    td = TextDetection(0.05)
    img = np.zeros((100, 100), dtype=np.uint8)
    
    mock_sobel.return_value = img
    mock_thresh.return_value = (None, img)
    mock_struct.return_value = MagicMock()
    mock_morph.return_value = img
    # Simulate findContours result (contours, hierarchy)
    # contour needs more than 4 points to pass noiseSizeParam ** 2 (which is 4)
    mock_find.return_value = ([np.zeros((10, 1, 2), dtype=np.int32)], None)
    mock_rect.return_value = (0, 0, 10, 10)
    
    rectP, rect = td.text_detect(img)
    
    assert len(rect) == 1
    assert len(rectP) == 1
    mock_find.assert_called_once()

@patch('cv2.imread')
@patch('manga_extractor.modules.detection.TextDetection.text_detect')
def test_textDetect_file(mock_detect, mock_imread):
    td = TextDetection(0.05)
    mock_imread.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_detect.return_value = ([], [])
    
    res = td.textDetect("image.jpg", "folder/")
    assert len(res) == 2
    mock_imread.assert_called_once()
