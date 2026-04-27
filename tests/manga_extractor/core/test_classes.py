from manga_extractor.core.classes import Page, Chapter, Text, Volume, Config

def test_page_initialization():
    page = Page("page1.jpg", 1)
    assert page.name == "page1.jpg"
    assert page.number == 1
    assert page.texts == []

def test_page_add_text():
    page = Page("page1.jpg", 1)
    text = Text("Hello", 0, 10, 10, 50, 50)
    page.addTexto(text)
    assert len(page.texts) == 1
    assert page.texts[0].text == "Hello"

def test_chapter_initialization():
    chapter = Chapter("Manga Name", "1", "10", "PT")
    assert chapter.name == "Manga Name"
    assert chapter.volume == "1"
    assert chapter.chapter == "10"
    assert chapter.language == "PT"
    assert chapter.pages == []

def test_chapter_add_page():
    chapter = Chapter("Manga Name", "1", "10", "PT")
    page = Page("page1.jpg", 1)
    chapter.addPagina(page)
    assert len(chapter.pages) == 1
    assert chapter.pages[0].name == "page1.jpg"

def test_volume_initialization():
    volume = Volume("Manga Name", "1", "PT")
    assert volume.name == "Manga Name"
    assert volume.volume == "1"
    assert volume.chapters == []

def test_config_initialization():
    config = Config("dir", manga="Manga")
    assert config.directory == "dir"
    assert config.manga == "Manga"
    assert config.getFolderInformation is True
