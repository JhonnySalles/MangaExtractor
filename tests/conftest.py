import pytest
from unittest.mock import MagicMock
from manga_extractor.core.classes import Operation

@pytest.fixture
def mock_window():
    m = MagicMock()
    key_mocks = {}
    def get_item(key):
        if key not in key_mocks:
            key_mocks[key] = MagicMock()
        return key_mocks[key]
    m.__getitem__.side_effect = get_item
    return m


@pytest.fixture
def operation_pt(mock_window):
    return Operation(
        base="base_path",
        nameManga="Test Manga",
        directory="E:/Proj/MangaExtractor/example",
        language="PT",
        window=mock_window
    )

@pytest.fixture
def operation_ja(mock_window):
    return Operation(
        base="base_path",
        nameManga="Test Manga JA",
        directory="E:/Proj/MangaExtractor/example_ja",
        language="JA",
        window=mock_window,
        furigana=True
    )
