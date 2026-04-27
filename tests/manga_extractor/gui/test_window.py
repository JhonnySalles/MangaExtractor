import pytest
import os
from unittest.mock import patch, MagicMock
from manga_extractor.gui.window import (
    acronymLanguage, load, validateFields, cleanFields, enableButtons, 
    disableButtons, findLastVolume, eventDirectory, thread_process, 
    thread_list_process, thread_copy_file
)
from manga_extractor.core.classes import Config, Operation

@pytest.fixture
def mock_window():
    with patch('manga_extractor.gui.window.window') as mock_win:
        mock_elements = {}
        def get_item(key):
            if key not in mock_elements:
                mock_elements[key] = MagicMock()
            return mock_elements[key]
        mock_win.__getitem__.side_effect = get_item
        yield mock_win

def test_acronym_language():
    assert acronymLanguage('Japonês') == 'ja'
    assert acronymLanguage('Inglês') == 'en'
    assert acronymLanguage('Português') == 'pt'
    assert acronymLanguage('Japonês (vertical)') == 'ja'

def test_load_operation():
    values = {
        '-BASE-': 'test_base',
        '-MANGA-': 'Manga Name',
        '-DIRECTORY-': 'C:/Manga',
        '-LANGUAGE-': 'Japonês (vertical)',
        '-VOLUME-': '1',
        '-CHAPTER-': '1',
        '-SCAN-': 'Scan',
        '-OCRTYPE-': 'Tesseract',
        '-TESSERACT_LOCATE-': 'C:/Tesseract',
        '-GET_NAME-': True,
        '-GET_INFORMATION-': True,
        '-FURIGANA-': True,
        '-ADDITIONAL_FILTER_FURIGANA-': True
    }
    
    with patch('manga_extractor.gui.window.window', MagicMock()):
        op = load(values)
        assert op.base == 'test_base'
        assert op.language == 'ja'
        assert op.verticalText is True
        assert op.furigana is True

def test_validate_fields_success(mock_window):
    values = {
        '-OCRTYPE-': 'Tesseract',
        '-TESSERACT_LOCATE-': 'C:/Tesseract/tesseract.exe',
        '-DIRECTORY-': 'C:/Manga',
        '-MANGA-': 'Manga',
        '-GET_NAME-': False,
        '-GET_INFORMATION-': False,
        '-BASE-': 'base',
        '-VOLUME-': '1',
        '-CHAPTER-': '1',
        '-SCAN-': 'Scan',
        '-LANGUAGE-': 'Português',
        '-FURIGANA-': False,
        '-ADDITIONAL_FILTER_FURIGANA-': False
    }
    with patch('os.path.isfile', return_value=True), \
         patch('os.path.exists', return_value=True), \
         patch('manga_extractor.gui.window.saveConfig'):
        assert validateFields(values) is True

def test_validate_fields_manga_name_missing(mock_window):
    values = {
        '-OCRTYPE-': 'WinOCR',
        '-DIRECTORY-': 'C:/Manga',
        '-MANGA-': '',
        '-GET_NAME-': False,
        '-GET_INFORMATION-': False,
        '-BASE-': 'base',
        '-LANGUAGE-': 'Português'
    }
    with patch('os.path.exists', return_value=True), \
         patch('manga_extractor.gui.window.alert') as mock_alert:
        assert validateFields(values) is False
        mock_alert.assert_called_with('Favor informar um nome!')

def test_validate_fields_base_missing(mock_window):
    values = {
        '-OCRTYPE-': 'WinOCR',
        '-DIRECTORY-': 'C:/Manga',
        '-MANGA-': 'Manga',
        '-GET_NAME-': True,
        '-GET_INFORMATION-': False,
        '-BASE-': '',
        '-LANGUAGE-': 'Português'
    }
    with patch('os.path.exists', return_value=True), \
         patch('manga_extractor.gui.window.alert') as mock_alert:
        assert validateFields(values) is False
        mock_alert.assert_called_with('Favor informar uma base!')

def test_clean_fields(mock_window):
    cleanFields()
    mock_window['-DIRECTORY-'].Update.assert_called_with('C:/')
    mock_window['-MANGA-'].Update.assert_called_with('')

def test_enable_buttons(mock_window):
    enableButtons()
    mock_window['-BTN_PROCESS-'].Update.assert_called()

def test_disable_buttons_lista(mock_window):
    disableButtons('LISTA')
    mock_window['-BTN_PROCESS-'].Update.assert_called_with(disabled=True)
    mock_window['-BTN_PROCESS_LIST-'].Update.assert_called_with(text='Parar processamento')

def test_find_last_volume(mock_window):
    with patch('manga_extractor.gui.window.findTable') as mock_find:
        mock_table = MagicMock()
        mock_table.lastVolume = "Vol 10"
        mock_find.return_value = mock_table
        findLastVolume("base", "manga", "ja")
        mock_window['-LASTVOLUME-'].Update.assert_called_with("Vol 10")

def test_thread_process_error(mock_window):
    mock_op = MagicMock()
    with patch('manga_extractor.gui.window.process', side_effect=Exception("Test Error")):
        thread_process(mock_op, mock_window)
        mock_window.write_event_value.assert_called_with('-THREAD_ERROR-', "Test Error")

def test_thread_list_process(mock_window):
    mock_op = MagicMock()
    mock_op.nameManga = "List Manga"
    with patch('manga_extractor.gui.window.process'):
        thread_list_process([[mock_op, 'status']], mock_window)
        mock_window.write_event_value.assert_called()

def test_thread_copy_file(mock_window):
    mock_op = MagicMock()
    mock_op.isTest = False
    mock_op.window = mock_window
    with patch('manga_extractor.gui.window.moveFilesDirectories'), \
         patch('manga_extractor.gui.window.printLog'):
        thread_copy_file(mock_op, "src", "dest", "Folder")
    mock_window.write_event_value.assert_called()

def test_event_directory_auto_parse(mock_window):
    import manga_extractor.gui.window as window_mod
    window_mod.LAST_DIRECTORY = None
    values = {"-DIRECTORY-": "new/path", "-LANGUAGE-": "Português", "-MANGA-": "Initial Manga"}
    with patch('os.path.exists', return_value=True), \
         patch('os.walk', return_value=iter([('root', ['SubManga'], [])])), \
         patch('manga_extractor.gui.window.readConfig', return_value=None), \
         patch('manga_extractor.gui.window.getDirectoryName', return_value="Auto Manga"), \
         patch('manga_extractor.gui.window.getDirectoryInformation') as mock_get_info, \
         patch('manga_extractor.gui.window.findLastVolume'):
        
        mock_info = MagicMock()
        mock_info.volume = "2"
        mock_get_info.return_value = mock_info
        eventDirectory(values)
        mock_window['-MANGA-'].Update.assert_called_with("Auto Manga")
        mock_window['-VOLUME-'].Update.assert_called_with("2")
