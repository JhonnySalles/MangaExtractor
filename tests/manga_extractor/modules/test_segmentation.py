import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os
import math

# Mock external dependencies before they are imported by segmentation.py
sys.modules['tensorflow'] = MagicMock()
sys.modules['imgio'] = MagicMock()
sys.modules['utils.fp'] = MagicMock()
sys.modules['core'] = MagicMock()

from manga_extractor.modules.segmentation import TextSegmenation

@pytest.fixture
def mock_segmentation_deps():
    with patch('manga_extractor.modules.segmentation.imgio') as mock_imgio, \
         patch('manga_extractor.modules.segmentation.fp') as mock_fp, \
         patch('manga_extractor.modules.segmentation.smt') as mock_smt, \
         patch('manga_extractor.modules.segmentation.tf') as mock_tf:
        yield mock_imgio, mock_fp, mock_smt, mock_tf

def test_segmentation_initialization(operation_pt):
    with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs: MagicMock() if name == 'core' else MagicMock()):
        ts = TextSegmenation(operation_pt)
        assert ts.operation == operation_pt

def test_dimensions_2d_slice():
    ts = TextSegmenation(None)
    s = (slice(10, 30), slice(40, 70))
    assert ts.dimensions_2d_slice(s) == (40, 10, 30, 20)

@patch('cv2.imread')
@patch('cv2.resize')
@patch('cv2.imwrite')
def test_resize(mock_write, mock_resize, mock_read):
    ts = TextSegmenation(None)
    mock_read.return_value = np.zeros((2000, 1000, 3), dtype=np.uint8)
    ts.resize("test.jpg")
    mock_resize.assert_called_once()
    mock_write.assert_called_once()

@patch('manga_extractor.modules.segmentation.smt.RLSO')
@patch('manga_extractor.utils.helpers.get_connected_components')
@patch('manga_extractor.utils.helpers.segment_into_lines')
@patch('manga_extractor.utils.helpers.draw_2d_slices')
def test_cleaned2segmented(mock_draw, mock_seg_lines, mock_get_cc, mock_rlso, operation_pt):
    ts = TextSegmenation(operation_pt)
    cleaned = np.zeros((100, 100), dtype=np.uint8)
    mock_rlso.return_value = cleaned
    mock_get_cc.return_value = [(slice(10, 20), slice(10, 20))]
    mock_seg_lines.return_value = (1.0, [slice(0, 10), slice(11, 20)], [slice(0, 10), slice(11, 20)])
    
    res = ts.cleaned2segmented(cleaned, 10)
    assert res.shape == (100, 100)
    mock_draw.assert_called()

def test_text_like_histogram_basic(operation_pt):
    ts = TextSegmenation(operation_pt)
    operation_pt.furiganaFilter = False
    assert ts.text_like_histogram(None, None, 10) is True

@patch('manga_extractor.modules.cleaning.binarize')
@patch('manga_extractor.modules.cleaning.form_canny_mask')
@patch('manga_extractor.utils.helpers.average_size')
@patch('manga_extractor.utils.helpers.form_mask')
@patch('scipy.ndimage.gaussian_filter')
def test_segment_image(mock_gaussian, mock_form_mask, mock_avg, mock_canny, mock_bin, operation_pt):
    ts = TextSegmenation(operation_pt)
    img = np.zeros((100, 100), dtype=np.uint8)
    
    mock_bin.return_value = np.zeros((100, 100), dtype=np.uint8)
    mock_avg.return_value = 10
    mock_form_mask.return_value = np.zeros((100, 100), dtype=np.uint8)
    mock_gaussian.return_value = np.zeros((100, 100), dtype=np.uint8)
    
    with patch.object(ts, 'cleaned2segmented') as mock_c2s, \
         patch.object(ts, 'filter_text_like_areas') as mock_filter:
        
        mock_c2s.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_filter.return_value = ([], []) 
        
        res = ts.segment_image(img)
        assert isinstance(res, np.ndarray)
        assert res.shape == (100, 100, 3)

def test_filter_text_like_areas(operation_ja):
    ts = TextSegmenation(operation_ja)
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    segmentation = np.zeros((100, 100), dtype=np.uint8)
    segmentation[10:30, 10:50] = 1
    
    with patch('manga_extractor.modules.segmentation.clean.binarize', return_value=segmentation), \
         patch('manga_extractor.modules.segmentation.util.get_connected_components', return_value=[(slice(10, 30), slice(10, 50))]), \
         patch.object(ts, 'text_like_histogram', return_value=True):
        
        text_areas, non_text = ts.filter_text_like_areas(img, segmentation, 10)
        assert len(text_areas) == 1
        assert len(non_text) == 0

def test_text_like_histogram_basic_ja(operation_ja):
    ts = TextSegmenation(operation_ja)
    operation_ja.furiganaFilter = True
    img = np.zeros((100, 100), dtype=np.uint8)
    area = (slice(10, 30), slice(10, 50))
    
    with patch('manga_extractor.modules.segmentation.util.get_connected_components', return_value=[MagicMock(), MagicMock()]), \
         patch('manga_extractor.modules.segmentation.util.average_size', return_value=10), \
         patch('manga_extractor.modules.segmentation.util.mean_width', return_value=10), \
         patch('manga_extractor.modules.segmentation.util.mean_height', return_value=10), \
         patch('manga_extractor.modules.segmentation.scipy.ndimage.filters.gaussian_filter', side_effect=lambda x, y: x), \
         patch.object(ts, 'get_white_runs', return_value=[1, 2, 3]), \
         patch.object(ts, 'get_black_runs', return_value=[1, 2, 3]), \
         patch.object(ts, 'slicing_list_stats', return_value=(5, 1)):
        
        res = ts.text_like_histogram(img, area, 10)
        assert res is True

@patch('manga_extractor.modules.cleaning.grayscale')
@patch('manga_extractor.modules.cleaning.binarize')
@patch('cv2.imread')
@patch('cv2.imwrite')
def test_segment_furigana(mock_write, mock_read, mock_bin, mock_gray, operation_pt):
    ts = TextSegmenation(operation_pt)
    mock_read.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_gray.return_value = np.zeros((100, 100), dtype=np.uint8)
    mock_bin.return_value = np.zeros((100, 100), dtype=np.uint8)
    
    with patch.object(ts, 'segment_image') as mock_seg_img:
        mock_seg_img.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        gray, cleaned, seg = ts.segmentFurigana("test.jpg", "out/")
        assert gray.shape == (100, 100)
        assert cleaned.shape == (100, 100)
        assert seg.shape == (100, 100)

def test_area_is_text_like(operation_pt):
    ts = TextSegmenation(operation_pt)
    img = np.zeros((100, 100), dtype=np.uint8)
    # Put some white pixels in a grid-like pattern
    img[10:50:10, 10:50] = 255
    img[10:50, 10:50:10] = 255
    area = (slice(10, 50), slice(10, 50))
    
    with patch('manga_extractor.modules.segmentation.util.average_size', return_value=10):
        # Normal case
        assert ts.area_is_text_like(img, area, 10) is True
        
        # Edge case: nan average size
        with patch('manga_extractor.modules.segmentation.util.average_size', return_value=math.nan):
            assert ts.area_is_text_like(img, area, 10) is False

def test_segment_page(operation_pt, mock_segmentation_deps):
    mock_imgio, mock_fp, mock_smt, mock_tf = mock_segmentation_deps
    ts = TextSegmenation(operation_pt)
    mock_read = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_imgio.load.return_value = mock_read
    mock_imgio.mask2segmap.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
    
    with patch.object(ts, 'imgpath2mask', return_value=np.zeros((100, 100))):
        ts.segmentPage("test.jpg", "inpainted/", "textonly/")
        mock_imgio.save.assert_called()
        mock_tf.device.assert_called_with('/gpu:0')
