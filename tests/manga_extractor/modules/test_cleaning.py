import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from manga_extractor.modules.cleaning import grayscale, binarize, clean_page

def test_grayscale():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    with patch('cv2.cvtColor') as mock_cvt:
        mock_cvt.return_value = np.zeros((100, 100), dtype=np.uint8)
        res = grayscale(img)
        assert res.shape == (100, 100)
        mock_cvt.assert_called_once()

def test_binarize():
    img = np.zeros((100, 100), dtype=np.uint8)
    with patch('cv2.threshold') as mock_thresh:
        mock_thresh.return_value = (127, np.zeros((100, 100), dtype=np.uint8))
        res = binarize(img)
        assert res.shape == (100, 100)
        mock_thresh.assert_called_once()

@patch('manga_extractor.modules.cleaning.grayscale')
@patch('manga_extractor.modules.cleaning.binarize')
@patch('scipy.ndimage.gaussian_filter')
@patch('manga_extractor.utils.helpers.average_size')
@patch('manga_extractor.utils.helpers.form_mask')
@patch('manga_extractor.modules.cleaning.form_canny_mask')
@patch('cv2.bitwise_not')
def test_clean_page(mock_bitwise, mock_canny, mock_form, mock_avg, mock_gauss, mock_bin, mock_gray):
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_gray.return_value = np.zeros((100, 100), dtype=np.uint8)
    mock_bin.return_value = np.zeros((100, 100), dtype=np.uint8)
    mock_gauss.return_value = np.zeros((100, 100), dtype=np.uint8)
    mock_avg.return_value = 10
    mock_form.return_value = np.zeros((100, 100), dtype=np.uint8)
    mock_canny.return_value = np.zeros((100, 100), dtype=np.uint8)
    mock_bitwise.return_value = np.zeros((100, 100), dtype=np.uint8)

    res = clean_page(img)
    assert len(res) == 3
    mock_gray.assert_called_once()
