import pytest
import os
import re
from unittest.mock import patch, MagicMock
from manga_extractor.core.processor import getDirectoryName, getDirectoryInformation, moveFilesDirectories

def test_get_directory_name():
    assert getDirectoryName("C:/Manga [JPN] - Volume 01") == "Manga"
    assert getDirectoryName("E:/Manga [ScanName] Volume 05") == "Manga"
    assert getDirectoryName("$Recycle.Bin") == ""
    # No underscore replacement in the code
    assert getDirectoryName("C:/Users/Scan/Manga_Name_Extra") == "Manga_Name_Extra"

def test_get_directory_information():
    chapter = getDirectoryInformation("Manga [Scan] Volume 1 Capítulo 10", "Manga", "PT")
    assert chapter.volume == "1"
    assert chapter.chapter == "10"
    assert chapter.scan == "Scan"
    assert chapter.isScan is True

def test_get_directory_information_extra():
    chapter = getDirectoryInformation("Manga Volume 1 Extra 1", "Manga", "PT")
    assert chapter.isExtra is True
    assert chapter.chapter == "1"

def test_get_directory_information_with_volume_keyword():
    # The code expects "volume" and "capitulo" keywords
    info = getDirectoryInformation("Manga Volume 05 Capitulo 12", "Manga", "PT")
    assert info.volume == "05"
    assert info.chapter == "12"
    
    info = getDirectoryInformation("Manga Volume 03 Extra 04", "Manga", "PT")
    assert info.volume == "03"
    assert info.chapter == "04"
    assert info.isExtra is True

def test_get_directory_information_with_scan():
    # Folder structure: root/Manga/[Scan]
    info = getDirectoryInformation("C:/Manga/[Scan_Name]", "Manga", "PT")
    assert info.scan == "Scan_Name"
    assert info.isScan is True

@patch('os.walk')
@patch('os.makedirs')
@patch('shutil.copy2')
def test_move_files_directories(mock_copy, mock_mkdir, mock_walk, operation_pt):
    # Mock os.walk result
    # root, dirs, files
    mock_walk.return_value = [
        ("orig/folder", [], ["Manga_v01_c01.jpg"])
    ]
    
    moveFilesDirectories(operation_pt, "orig", "dest", "Manga")
    
    # Check if makedirs was called for the new folder
    mock_mkdir.assert_called()
    # Check if copy2 was called
    mock_copy.assert_called_once()
