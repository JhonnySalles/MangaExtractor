import pytest
import os
import threading
from unittest.mock import patch, MagicMock
from manga_extractor.gui.window import validateFields, eventManga, eventDirectory, acronymLanguage, main
import manga_extractor.core.globals as globals
import FreeSimpleGUI as sg

@pytest.fixture
def mock_window_elements():
    # Patching window AND the global elements pointing to its keys
    # to avoid "finalize" errors and attribute errors on real FreeSimpleGUI objects.
    with patch('manga_extractor.gui.window.window') as mock_win, \
         patch('manga_extractor.gui.window.PROGRESS') as mock_progress, \
         patch('manga_extractor.gui.window.LOGMEMO') as mock_logmemo:
        
        mock_elements = {}
        def get_item(key):
            if key not in mock_elements:
                mock_elements[key] = MagicMock()
            return mock_elements[key]
        mock_win.__getitem__.side_effect = get_item
        
        # Make the mocked globals return something when their methods are called
        mock_progress.UpdateBar = MagicMock()
        mock_logmemo.Update = MagicMock()
        
        yield mock_win, mock_elements

def main_loop_with_events(mock_win, events):
    # events is a list of (event, values) tuples
    mock_events = events + [(sg.WIN_CLOSED, {})]
    mock_win.read.side_effect = mock_events
    main()

def test_gui_remove_operation(mock_window_elements):
    mock_win, mock_elements = mock_window_elements
    from manga_extractor.gui.window import listOperations
    listOperations.clear()
    listOperations.append([MagicMock(), "base", "manga", "dir", False, "PT", "-"])
    
    # Remove with selection
    main_loop_with_events(mock_win, [('-TABLE-', {'-TABLE-': [0]}), ('-BTN_REMOVE-', {'-TABLE-': [0]})])
    assert len(listOperations) == 0

def test_gui_process_list_empty(mock_window_elements):
    mock_win, mock_elements = mock_window_elements
    from manga_extractor.gui.window import listOperations
    listOperations.clear()
    with patch('manga_extractor.gui.window.alert') as mock_alert, \
         patch('manga_extractor.gui.window.testConnection', return_value=True):
        main_loop_with_events(mock_win, [('-BTN_PROCESS_LIST-', {})])
        mock_alert.assert_called_with('Nenhuma operação na lista.')

def test_gui_copy_files(mock_window_elements):
    mock_win, mock_elements = mock_window_elements
    with patch('manga_extractor.gui.window.threading.Thread') as mock_thread, \
         patch('manga_extractor.gui.window.testConnection', return_value=True):
        main_loop_with_events(mock_win, [('-BTN_COPY_FILES-', {'-TO_PATH-': 'to', '-FROM_PATH-': 'from', '-FOLDER_NAME-': 'folder'})])
        mock_thread.assert_called_once()

def test_gui_thread_events(mock_window_elements):
    mock_win, mock_elements = mock_window_elements
    with patch('manga_extractor.gui.window.alert') as mock_alert, \
         patch('manga_extractor.gui.window.OPERATION') as mock_op:
        main_loop_with_events(mock_win, [
            ('-THREAD_AVISO-', {'-THREAD_AVISO-': 'Some Warning'}),
            ('-THREAD_ERROR-', {'-THREAD_ERROR-': 'Some Error'}),
            ('-THREAD_PROGRESSBAR_UPDATE-', {'-THREAD_PROGRESSBAR_UPDATE-': 50}),
            ('-THREAD_PROGRESSBAR_MAX-', {'-THREAD_PROGRESSBAR_MAX-': 100})
        ])
        assert mock_alert.call_count == 2

def test_gui_thread_end_cancel(mock_window_elements):
    mock_win, mock_elements = mock_window_elements
    globals.CANCEL_OPERATION = True
    with patch('manga_extractor.gui.window.alert') as mock_alert, \
         patch('manga_extractor.gui.window.OPERATION') as mock_op:
        main_loop_with_events(mock_win, [('-THREAD_END-', {'-THREAD_END-': 'Done'})])
        mock_alert.assert_called_with('Processamento parado.')
    globals.CANCEL_OPERATION = False

def test_gui_language_change_logic(mock_window_elements):
    mock_win, mock_elements = mock_window_elements
    with patch('manga_extractor.gui.window.eventFindLastVolume'):
        main_loop_with_events(mock_win, [('-LANGUAGE-', {'-LANGUAGE-': 'Português'})])
        mock_win['-FURIGANA-'].update.assert_called_with(value=False, disabled=True)
        
        main_loop_with_events(mock_win, [('-LANGUAGE-', {'-LANGUAGE-': 'Japonês'})])
        mock_win['-FURIGANA-'].update.assert_called_with(disabled=False)

def test_gui_process_cancel(mock_window_elements):
    mock_win, mock_elements = mock_window_elements
    mock_win['-BTN_PROCESS-'].get_text.return_value = 'Parar processamento'
    main_loop_with_events(mock_win, [('-BTN_PROCESS-', {})])
    assert globals.CANCEL_OPERATION is True
    globals.CANCEL_OPERATION = False

def test_gui_insert_operation(mock_window_elements):
    mock_win, mock_elements = mock_window_elements
    from manga_extractor.gui.window import listOperations
    listOperations.clear()
    with patch('manga_extractor.gui.window.validateFields', return_value=True), \
         patch('manga_extractor.gui.window.load') as mock_load:
        mock_op = MagicMock()
        mock_op.base = "base"
        mock_op.nameManga = "Manga"
        mock_op.directory = "dir"
        mock_op.furigana = False
        mock_op.language = "PT"
        mock_load.return_value = mock_op
        
        main_loop_with_events(mock_win, [('-BTN_INSERT-', {})])
        assert len(listOperations) == 1
