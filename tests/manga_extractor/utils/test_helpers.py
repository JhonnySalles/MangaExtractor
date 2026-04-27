import numpy as np
from manga_extractor.utils.helpers import area_bb, width_bb, height_bb

def test_area_bb():
    # slices are (y, x)
    a = (slice(10, 20), slice(30, 50))
    # height = 10, width = 20 -> area = 200
    assert area_bb(a) == 200

def test_width_bb():
    a = (slice(10, 20), slice(30, 50))
    assert width_bb(a) == 20
    
def test_height_bb():
    a = (slice(10, 20), slice(30, 50))
    assert height_bb(a) == 10

def test_area_bb_empty():
    a = (slice(20, 10), slice(30, 50))
    assert area_bb(a) == 0

def test_config_io(tmp_path):
    from manga_extractor.core.classes import Config
    from manga_extractor.utils.helpers import saveConfig, readConfig
    
    config_dir = str(tmp_path)
    config = Config(config_dir, "Manga", "1", "1", "Scan", "Base", "PT", "Tesseract")
    
    saveConfig(config)
    loaded = readConfig(config_dir)
    
    assert loaded.manga == "Manga"
    assert loaded.base == "Base"
    assert loaded.ocr == "Tesseract"

def test_average_size():
    from manga_extractor.utils.helpers import average_size
    img = np.zeros((100, 100), dtype=np.uint8)
    # Create two components of 10x10 size
    img[10:20, 10:20] = 255
    img[40:50, 40:50] = 255
    
    # average_size takes sqrt(area_bb) = sqrt(100) = 10
    assert average_size(img, minimum_area=3, maximum_area=110) == 10

def test_segment_into_lines():
    from manga_extractor.utils.helpers import segment_into_lines
    img = np.zeros((100, 100), dtype=np.uint8)
    # Two vertical lines
    img[10:90, 10:20] = 255
    img[10:90, 30:40] = 255
    
    component = (slice(10, 90), slice(10, 40))
    aspect, vertical, horizontal = segment_into_lines(img, component)
    
    assert len(vertical) == 2
    assert len(horizontal) == 1

def test_print_log_to_file(tmp_path):
    from manga_extractor.utils.helpers import printLog
    from manga_extractor.core.classes import PrintLog
    
    log_dir = str(tmp_path)
    log_obj = PrintLog("Test Message", directory=log_dir, isTest=True, save=True)
    
    printLog(log_obj, file='test_log.txt')
    
    log_file = tmp_path / 'test_log.txt'
    assert log_file.exists()
    assert "Test Message" in log_file.read_text(encoding='utf-8')

def test_filter_by_black_white_ratio():
    from manga_extractor.utils.helpers import filter_by_black_white_ratio
    img = np.zeros((100, 100), dtype=np.uint8)
    img[10:20, 10:20] = 255 # 100 pixels black
    
    components = [(slice(10, 20), slice(10, 20))]
    # Ratio is 1.0 (all non-zero in bounding box)
    filtered = filter_by_black_white_ratio(img, components, maximum=1.1, minimum=0.5)
    assert len(filtered) == 1
    
    filtered_out = filter_by_black_white_ratio(img, components, maximum=0.5, minimum=0.0)
    assert len(filtered_out) == 0

def test_bounding_boxes():
    from manga_extractor.utils.helpers import bounding_boxes
    img = np.zeros((100, 100), dtype=np.uint8)
    components = [(slice(10, 20), slice(10, 20))]
    
    mask = bounding_boxes(img, components, max_size=50, min_size=5)
    assert mask[15, 15] == 1
    assert mask[5, 5] == 0

def test_mean_width_height():
    from manga_extractor.utils.helpers import mean_width, mean_height
    img = np.zeros((100, 100), dtype=np.uint8)
    # Component 10x20
    img[10:20, 10:30] = 255
    
    assert mean_width(img, minimum=5, maximum=50) == 20
    assert mean_height(img, minimum=5, maximum=50) == 10


def test_print_log_colors(mock_window):
    from manga_extractor.utils.helpers import printLog
    from manga_extractor.core.classes import PrintLog
    
    colors = ['green', 'yellow', 'red', 'blue', 'magenta']
    for color in colors:
        log_obj = PrintLog(f"Test {color}", color=color, logMemo=mock_window, isTest=False, isSilent=False)
        printLog(log_obj)

        # Verify color mapping
        mock_window.print.assert_called()

def test_read_config_error(tmp_path):
    from manga_extractor.utils.helpers import readConfig
    config_file = tmp_path / "config.ini"
    config_file.write_text("[operation]\ninvalid=content")
    
    # Should return None on missing fields
    assert readConfig(str(tmp_path)) is None

def test_read_config_unicode_fallback(tmp_path):
    from manga_extractor.utils.helpers import readConfig
    config_file = tmp_path / "config.ini"
    # Write with latin-1 encoding
    content = "[operation]\ndirectory=C:/Manga\nmanga=Manga\nvolume=1\nchapter=1\nscan=Scan\nbase=Base\nlanguage=PT\nocr=Tesseract\nfolder_information=True\nname_folder=True\nclean_furigana=False\nfurigana_filter=False"
    with open(config_file, 'w', encoding='latin-1') as f:
        f.write(content)
        
    loaded = readConfig(str(tmp_path))
    assert loaded is not None
    assert loaded.manga == "Manga"

def test_masks():
    from manga_extractor.utils.helpers import masks
    img = np.zeros((100, 100), dtype=np.uint8)
    img[10:20, 10:20] = 255
    components = [(slice(10, 20), slice(10, 20))]
    
    mask = masks(img, components, max_size=50, min_size=5)
    assert np.any(mask == 1)

def test_draw_helpers():
    from manga_extractor.utils.helpers import draw_bounding_boxes, draw_2d_slices
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    components = [(slice(10, 20), slice(10, 20))]
    
    draw_bounding_boxes(img, components)
    assert np.any(img > 0)
    
    img_slices = np.zeros((100, 100, 3), dtype=np.uint8)
    draw_2d_slices(img_slices, components)
    assert np.any(img_slices > 0)

def test_area_nz():
    from manga_extractor.utils.helpers import area_nz
    img = np.zeros((100, 100), dtype=np.uint8)
    img[10:20, 10:20] = 255
    comp = (slice(10, 20), slice(10, 20))
    assert area_nz(comp, img) == 100

def test_filter_by_size():
    from manga_extractor.utils.helpers import filter_by_size
    components = [
        (slice(0, 10), slice(0, 10)),  # size 100, sqrt 10
        (slice(0, 2), slice(0, 2)),    # size 4, sqrt 2
        (slice(0, 50), slice(0, 50))   # size 2500, sqrt 50
    ]
    
    # Filter for sqrt size between 5 and 20
    filtered = filter_by_size(None, components, max_size=20, min_size=5)
    assert len(filtered) == 1
    assert filtered[0][0].stop == 10
