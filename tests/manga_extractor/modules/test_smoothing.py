import pytest
import numpy as np
from manga_extractor.modules.smoothing import vertical_run_length_smoothing, horizontal_run_lendth_smoothing, RLSO

def test_vertical_run_length_smoothing():
    # 5x5 image with two dots separated by 2 pixels
    img = np.zeros((5, 5), dtype=np.uint8)
    img[0, 0] = 255
    img[3, 0] = 255
    
    # Threshold 3 should bridge the gap (distance is 2 pixels between dots)
    res = vertical_run_length_smoothing(img, 3)
    assert res[1, 0] == 255
    assert res[2, 0] == 255
    
    # Threshold 1 should NOT bridge the gap
    res2 = vertical_run_length_smoothing(img, 1)
    assert res2[1, 0] == 0

def test_horizontal_run_length_smoothing():
    img = np.zeros((5, 5), dtype=np.uint8)
    img[0, 0] = 255
    img[0, 3] = 255
    
    res = horizontal_run_lendth_smoothing(img, 3)
    assert res[0, 1] == 255
    assert res[0, 2] == 255
    
    res2 = horizontal_run_lendth_smoothing(img, 1)
    assert res2[0, 1] == 0

def test_rlso():
    img = np.zeros((5, 5), dtype=np.uint8)
    img[0, 0] = 255
    img[3, 0] = 255 # vertical gap
    img[0, 3] = 255 # horizontal gap
    
    res = RLSO(img, 3, 3)
    assert res[1, 0] == 255 # vertical bridge
    assert res[0, 1] == 255 # horizontal bridge
