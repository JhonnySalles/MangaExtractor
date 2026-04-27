import pytest
import os
import uuid
from unittest.mock import patch, MagicMock
from manga_extractor.database.db_util import BdUtil, findTable, testConnection as db_test_connection, saveData
from mysql.connector.errors import ProgrammingError

@pytest.fixture
def mock_db_connection():
    with patch('manga_extractor.database.db_util.conection') as mock_conn_func:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn_func.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 0
        yield mock_conn, mock_cursor

def test_bd_util_exist_table(operation_pt, mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.rowcount = 1
    util = BdUtil(operation_pt)
    assert util.existTable("test_table") is True

def test_bd_util_last_volume(operation_pt, mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.rowcount = 1
    mock_cursor.fetchone.return_value = (5, "Manga Name")
    util = BdUtil(operation_pt)
    res = util.lastVolume("table", "Manga", "PT")
    assert "Último volume 5" in res

def test_bd_util_create_table(operation_pt, mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.rowcount = 0 
    util = BdUtil(operation_pt)
    res = util.createTable("New Manga")
    assert res == "New_Manga"

def test_bd_util_save_volume(operation_pt, mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.rowcount = 0 
    from manga_extractor.core.classes import Volume, Chapter
    volume = Volume("Manga", "1", "PT")
    volume.chapters = [Chapter("Manga", "1", "1", "PT")]
    util = BdUtil(operation_pt)
    with patch.object(util, 'saveChapter'), patch.object(util, 'saveCover'):
        util.saveVolume(volume)
        mock_cursor.execute.assert_called()

def test_save_chapter(operation_pt, mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    util = BdUtil(operation_pt)
    from manga_extractor.core.classes import Chapter, Page
    chapter = Chapter("Manga", "1", "1", "PT")
    chapter.pages = [Page("p1.jpg", 1)]
    mock_cursor.rowcount = 1
    mock_cursor.fetchone.return_value = (str(uuid.uuid4()),)
    with patch.object(util, 'deleteChapter'), patch.object(util, 'savePage'):
        util.saveChapter("vol_id", chapter)
        assert mock_cursor.execute.call_count >= 2

def test_save_page(operation_pt, mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    util = BdUtil(operation_pt)
    from manga_extractor.core.classes import Page, Text
    page = Page("p1.jpg", 1)
    page.texts = [Text("hello", 0, 0, 0, 10, 10)]
    mock_cursor.rowcount = 0
    with patch.object(util, 'saveText'):
        util.savePage("chap_id", page)
        assert mock_cursor.execute.call_count >= 2

def test_save_text(operation_pt, mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    util = BdUtil(operation_pt)
    from manga_extractor.core.classes import Text
    text = Text("hello", 0, 0, 0, 10, 10)
    mock_cursor.rowcount = 0
    util.saveText("page_id", text)
    mock_cursor.execute.assert_called()

def test_save_cover(operation_pt, mock_db_connection, tmp_path):
    mock_conn, mock_cursor = mock_db_connection
    from manga_extractor.core.classes import Volume, Cover
    cover_file = tmp_path / "cover.jpg"
    cover_file.write_bytes(b"data")
    vol = Volume("Manga", "1", "PT")
    vol.cover = Cover("cover.jpg", "jpg", str(cover_file), str(tmp_path))
    mock_cursor.rowcount = 0
    util = BdUtil(operation_pt)
    util.saveCover("vol_id", vol)
    assert vol.cover.saved is True

def test_delete_chapter(operation_pt, mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.rowcount = 1
    mock_cursor.__iter__.return_value = [("chap_id",)]
    util = BdUtil(operation_pt)
    util.deleteChapter("id")
    assert mock_cursor.execute.call_count >= 2

def test_error_handling(operation_pt, mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = ProgrammingError(msg="Error")
    util = BdUtil(operation_pt)
    assert util.existTable("test") is False

def test_test_connection_mocked():
    with patch('manga_extractor.database.db_util.conection') as mock_conn_func:
        mock_conn = MagicMock()
        mock_conn_func.return_value.__enter__.return_value = mock_conn
        mock_conn.is_connected.return_value = True
        assert db_test_connection() is True

def test_find_table(mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.rowcount = 1
    mock_cursor.fetchone.return_value = (1, "Manga")
    res = findTable("Title", "Manga", "PT")
    assert res.exists is True

def test_save_data(operation_pt):
    operation_pt.base = "test"
    with patch('manga_extractor.database.db_util.BdUtil.saveVolume') as mock_save:
        saveData(operation_pt, MagicMock(), MagicMock())
        mock_save.assert_called_once()

def test_exist_table_none(operation_pt):
    util = BdUtil(operation_pt)
    with pytest.raises(ValueError, match="Tabela não informada."):
        util.existTable(None)

def test_last_volume_error(operation_pt, mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = ProgrammingError(msg="DB Error")
    util = BdUtil(operation_pt)
    res = util.lastVolume("table", "Manga", "PT")
    assert "Erro na verificação do último volume" in res


def test_save_cover_failures(operation_pt, mock_db_connection):
    util = BdUtil(operation_pt)
    # Case 1: ID is None
    util.saveCover(None, MagicMock())
    # Case 2: volume.cover is None
    util.saveCover("id", MagicMock(cover=None))
    # Case 3: cover.saved is True
    cover = MagicMock(saved=True)
    util.saveCover("id", MagicMock(cover=cover))
    # Case 4: cover file not exists
    cover.saved = False
    cover.file = "non_existent.jpg"
    with patch('os.path.exists', return_value=False):
        util.saveCover("id", MagicMock(cover=cover))

def test_save_text_failures(operation_pt, mock_db_connection):
    util = BdUtil(operation_pt)
    # id_page None or text None
    util.saveText(None, MagicMock())
    util.saveText("id", None)

def test_save_page_failures(operation_pt, mock_db_connection):
    util = BdUtil(operation_pt)
    # id_chapter None or page None
    util.savePage(None, MagicMock())
    util.savePage("id", None)

def test_save_chapter_failures(operation_pt, mock_db_connection):
    util = BdUtil(operation_pt)
    # id_volume None or chapter None
    util.saveChapter(None, MagicMock())
    util.saveChapter("id", None)

def test_delete_chapter_failures(operation_pt, mock_db_connection):
    util = BdUtil(operation_pt)
    # id_chapter None
    util.deleteChapter(None)

def test_save_data_base_none(operation_pt):
    operation_pt.base = None
    with pytest.raises(ValueError, match="Erro ao gravar os dados, table não informada."):
        saveData(operation_pt, MagicMock(), MagicMock())

def test_programming_error_handling_various(operation_pt, mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.execute.side_effect = ProgrammingError(msg="Generic Error")
    util = BdUtil(operation_pt)
    
    # savePage error
    util.savePage("id", MagicMock(texts=[]))
    # saveChapter error
    util.saveChapter("id", MagicMock(pages=[]))
    # deleteChapter error (initial select)
    util.deleteChapter("id")
    # saveCover error (binary open handled via mock, let's mock open to fail)
    vol = MagicMock()
    vol.cover = MagicMock(saved=False)
    vol.cover.file = "fake.jpg"
    with patch('os.path.exists', return_value=True), patch('builtins.open', side_effect=ProgrammingError(msg="File Error")):
         util.saveCover("id", vol)

