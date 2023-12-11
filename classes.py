import defaults
import os

class Cover:
    def __init__(self, fileName, extension, file):
        pass
        self.fileName = fileName
        self.extension = extension
        self.file = file
        self.saved = False


class Text:
    def __init__(self, text, sequence, posX1, posY1, posX2, posY2):
        pass
        self.text = text
        self.sequence = sequence
        self.posX1 = posX1
        self.posY1 = posY1
        self.posX2 = posX2
        self.posY2 = posY2


class Page:
    def __init__(self, name, number=0):
        pass
        self.name = name
        self.number = number
        self.hashPage = ""
        self.file = ""
        self.texts = []

    def addTexto(self, text):
        self.texts.append(text)

class Chapter:
    def __init__(self, name, volume, chapter, language):
        pass
        self.name = name
        self.volume = volume
        self.chapter = chapter
        self.language = language
        self.pages = []
        self.scan = ""
        self.isScan = False
        self.isExtra = False

    def addPagina(self, text):
        self.pages.append(text)

class Volume:
    def __init__(self, name, volume, language, chapter=None, cover=None):
        pass
        self.name = name
        self.volume = volume
        self.language = language
        self.chapters = []
        self.cover = cover
        if chapter is not None:
            self.chapters.append(chapter) 
            

    def addCapitulo(self, text):
        self.chapters.append(text)


class PrintLog:
    def __init__(self, message, color=None, save=True, logMemo=None, isTest=False, directory=None, isSilent=False):
        pass
        self.message = message
        self.color = color
        self.save = save
        self.directory = directory
        self.isSilent = isSilent
        self.isTest = isTest
        self.logMemo = logMemo


class Operation:
    def __init__(self, base, nameManga, directory, language, window=None, ocrType='tesseract', furigana=False, isSilent=False):
        pass
        self.nameManga = nameManga
        self.directory = directory.replace('\\', '/')
        self.language = language.lower()
        self.verticalText = None
        self.volume = None
        self.chapter = None
        self.scan = None
        self.base = base
        self.getFolderInformation = True
        self.getNameFolder = True
        self.furigana = furigana
        self.furiganaFilter = False
        self.ocrType = ocrType
        self.tesseractFolder = defaults.DEFAULT_TESSERACT_FOLDER
        self.isTest = window is None
        self.isSilent = isSilent
        self.applicationPath = os.path.abspath('')
        self.window = window

        if not self.isTest:
            self.logMemo = window['-OUTPUT-']
            self.progress = window['-PROGRESSBAR-']


class Config:
    def __init__(self, directory, manga='', volume='', chapter='', scan='', base='', language='', ocr='', getFolderInformation=True, getNameFolder=True, isCleanFurigana=False, isFuriganaFilter=False):
        pass
        self.directory = directory
        self.manga = manga
        self.volume = volume
        self.chapter = chapter
        self.scan = scan
        self.base = base
        self.language = language
        self.ocr = ocr
        self.getFolderInformation = getFolderInformation
        self.getNameFolder = getNameFolder
        self.isCleanFurigana = isCleanFurigana
        self.isFuriganaFilter = isFuriganaFilter