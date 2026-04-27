import pytest
import os
import cv2
import numpy as np
from manga_extractor.modules.segmentation import TextSegmenation
from manga_extractor.modules.ocr import TextOcr

from manga_extractor.core.classes import Operation

@pytest.mark.integration
def test_full_pipeline_on_real_image(operation_ja, tmp_path):
    # Setup paths
    fixture_path = os.path.join("tests", "fixtures", "images", "05_117.jpg")
    if not os.path.exists(fixture_path):
        pytest.skip("Fixture image not found")
        
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # 1. Segmentation
    # Check if model exists
    model_path = os.path.join("lib", "SickZil-Machine", "resource", "snet", "snet-0.1.0.pb")
    if not os.path.exists(model_path):
        pytest.skip("SickZil model not found at " + model_path)
        
    ts = TextSegmenation(operation_ja)

    # segment_image returns (img_bgr, text_areas, non_text_areas)
    # Actually, looking at previous viewed code, segment_image returns an ndarray (segmentation mask)
    img = cv2.imread(fixture_path)
    segmentation = ts.segment_image(img)
    
    assert isinstance(segmentation, np.ndarray)
    assert segmentation.shape == img.shape
    
    # 2. Filter text areas
    text_areas, non_text = ts.filter_text_like_areas(img, segmentation[:,:,2], 10)
    assert len(text_areas) > 0
    
    # 3. OCR (Check if tesseract is available)
    ocr = TextOcr(operation_ja)

    # We can try to OCR the first area
    if len(text_areas) > 0:
        area = text_areas[0]
        # Get slice
        y1, x1, y2, x2 = ts.dimensions_2d_slice(area)
        roi = img[y1:y2, x1:x2]
        
        # Test OCR if possible
        try:
            text = ocr.ocr_image(roi)
            # 05_117.jpg has Japanese text. Even if OCR is not perfect, 
            # it should return some string if tesseract is working.
            assert isinstance(text, str)
        except Exception as e:
            if "tesseract" in str(e).lower():
                pytest.skip("Tesseract not installed or not in PATH")
            else:
                raise e

@pytest.mark.integration
def test_processor_metadata_extraction():
    from manga_extractor.core.processor import getDirectoryInformation
    # Integration test for folder parsing logic with various real-world patterns
    paths = [
        "Manga Name/Volume 01/Capítulo 10/01.jpg",
        "Manga_Name_Vol_02_Cap_05/p01.png",
        "Manga [Volume 3] (Capitulo 15)/img.webp"
    ]
    
    for p in paths:
        chapter_obj = getDirectoryInformation(p, "Manga Name")
        assert chapter_obj.volume is not None
        assert chapter_obj.chapter is not None

