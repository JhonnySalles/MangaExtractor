import pytest
import os
import shutil
from unittest.mock import patch, MagicMock
from manga_extractor.core.processor import ImageProcess
from manga_extractor.core.classes import Chapter, Page, Cover

@pytest.fixture
def image_process(operation_pt):
    return ImageProcess(operation_pt)

def test_image_process_initialization(image_process, operation_pt):
    assert image_process.operation == operation_pt
    assert image_process.language == operation_pt.language
    assert "tmp/" in image_process.tempFolder

@patch('os.path.exists')
@patch('os.makedirs')
@patch('shutil.rmtree')
def test_clean_directories(mock_rmtree, mock_makedirs, mock_exists, image_process):
    mock_exists.return_value = True
    image_process.cleanDirectories()
    assert mock_rmtree.call_count == 3
    assert mock_makedirs.call_count == 3

@patch('hashlib.md5')
@patch('builtins.open', new_callable=MagicMock)
def test_create_class_page(mock_open, mock_md5, image_process):
    mock_md5_instance = mock_md5.return_value
    mock_md5_instance.hexdigest.return_value = "fake_hash"
    
    page = image_process.createClassPage("dir", "file.jpg", 1)
    
    assert page.name == "file.jpg"
    assert page.number == 1
    assert page.hashPage == "fake_hash"

def test_create_class_chapter_with_folder_info(image_process):
    image_process.operation.getFolderInformation = True
    with patch('manga_extractor.core.processor.getDirectoryInformation') as mock_get_info:
        mock_get_info.return_value = Chapter("Manga", "1", "1", "PT")
        chapter = image_process.createClassChapter("some/dir")
        assert chapter.name == "Manga"
        mock_get_info.assert_called_once()

def test_create_class_chapter_without_folder_info(image_process):
    image_process.operation.getFolderInformation = False
    image_process.operation.volume = "5"
    image_process.operation.chapter = "10"
    image_process.operation.scan = "ScanGroup"
    
    chapter = image_process.createClassChapter("some/dir")
    assert chapter.volume == "5"
    assert chapter.chapter == "10"
    assert chapter.scan == "ScanGroup"

@patch('PIL.Image.open')
def test_create_class_cover(mock_image_open, image_process):
    mock_img = MagicMock()
    mock_img.size = (1000, 1000)
    mock_image_open.return_value.__enter__.return_value = mock_img
    
    cover = image_process.createClassCover("dir", "frente.jpg")
    
    assert cover.fileName == "frente.jpg"
    assert cover.extension == "jpg"
    assert "capa.jpg" in cover.file
    mock_img.thumbnail.assert_called()
    mock_img.convert.assert_called_with('RGB')

@patch('os.walk')
@patch('os.listdir')
@patch('os.path.exists')
@patch('os.mkdir')
@patch('os.rename')
@patch('shutil.move')
@patch('manga_extractor.core.processor.TextSegmenation')
@patch('manga_extractor.core.processor.TextDetection')
@patch('manga_extractor.core.processor.TextOcr')
@patch('manga_extractor.core.processor.RemoveFurigana')
@patch('manga_extractor.database.db_util.saveData')
def test_process_images_full_flow(
    mock_save_data, mock_furigana, mock_ocr, mock_detection, mock_segmentation,
    mock_move, mock_rename, mock_mkdir, mock_exists, mock_listdir, mock_walk,
    image_process
):
    # Setup mocks
    mock_exists.return_value = False # For 'concluido' folder
    mock_listdir.return_value = ["page1.jpg"]
    
    # Mock os.walk(self.folder)
    # first call for renaming
    # second call for processing
    mock_walk.side_effect = [
        [("dir", ["sub"], ["page1.jpg"])], # First loop (rename)
        [("dir", [], ["page1.jpg"])]       # Second loop (process)
    ]
    
    # Mock components
    mock_seg_instance = mock_segmentation.return_value
    mock_det_instance = mock_detection.return_value
    mock_ocr_instance = mock_ocr.return_value
    
    # Mock helper methods of image_process to avoid complex logic
    with patch.object(image_process, 'cleanDirectories'), \
         patch.object(image_process, 'createClassChapter') as mock_create_chap, \
         patch.object(image_process, 'createClassPage') as mock_create_page:
        
        mock_create_chap.return_value = Chapter("Manga", "1", "1", "PT")
        mock_create_page.return_value = Page("page1.jpg", 1)
        
        image_process.processImages()
        
        # Verify calls
        mock_seg_instance.segmentPage.assert_called()
        mock_det_instance.textDetect.assert_called()
        mock_ocr_instance.getTextFromImg.assert_called()
        mock_save_data.assert_called()
        mock_move.assert_called()
