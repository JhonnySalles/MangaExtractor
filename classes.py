import defaults
import os

class Texto:
    def __init__(self, texto, sequencia, posX1, posY1, posX2, posY2):
        pass
        self.texto = texto
        self.sequencia = sequencia
        self.posX1 = posX1
        self.posY1 = posY1
        self.posX2 = posX2
        self.posY2 = posY2


class Pagina:
    def __init__(self, nome, numero=0):
        pass
        self.nome = nome
        self.numero = numero
        self.hashPagina = ""
        self.arquivo = ""
        self.textos = []

    def addTexto(self, texto):
        self.textos.append(texto)

class Capitulo:
    def __init__(self, nome, volume, capitulo, linguagem):
        pass
        self.nome = nome
        self.volume = volume
        self.capitulo = capitulo
        self.linguagem = linguagem
        self.paginas = []
        self.scan = ""
        self.isScan = False
        self.isExtra = False

    def addPagina(self, texto):
        self.paginas.append(texto)

class Volume:
    def __init__(self, nome, volume, linguagem, capitulo=None):
        pass
        self.nome = nome
        self.volume = volume
        self.linguagem = linguagem
        self.capitulos = []
        if capitulo is not None:
            self.capitulos.append(capitulo) 

    def addCapitulo(self, texto):
        self.capitulos.append(texto)


class PrintLog:
    def __init__(self, mensagem, cor=None, save=True, logMemo=None, isTeste=False, caminho=None, isSilent=False):
        pass
        self.mensagem = mensagem
        self.cor = cor
        self.save = save
        self.caminho = caminho
        self.isSilent = isSilent
        self.isTeste = isTeste
        self.logMemo = logMemo


class Operacao:
    def __init__(self, base, mangaNome, caminho, linguagem, window=None, ocrType='tesseract', furigana=False, isSilent=False):
        pass
        self.mangaNome = mangaNome
        self.caminho = caminho.replace('\\', '/')
        self.linguagem = linguagem.lower()
        self.textoVertical = None
        self.volume = None
        self.capitulo = None
        self.scan = None
        self.base = base
        self.getInformacaoPasta = True
        self.getNomePasta = True
        self.furigana = furigana
        self.filtroAdicional = False
        self.ocrType = ocrType
        self.pastaTesseract = defaults.DEFAULT_TESSERACT_FOLDER
        self.isTeste = window is None
        self.isSilent = isSilent
        self.caminhoAplicacao = os.path.abspath('')
        self.window = window

        if not self.isTeste:
            self.logMemo = window['-OUTPUT-']
            self.progress = window['-PROGRESSBAR-']


class Config:
    def __init__(self, directory, manga='', volume='', chapter='', scan='', base='', language='', ocr='', isReadInformationFolder=True, isMangaNameFolder=True, isCleanFurigana=False, isFuriganaFilter=False):
        pass
        self.directory = directory
        self.manga = manga
        self.volume = volume
        self.chapter = chapter
        self.scan = scan
        self.base = base
        self.language = language
        self.ocr = ocr
        self.isReadInformationFolder = isReadInformationFolder
        self.isMangaNameFolder = isMangaNameFolder
        self.isCleanFurigana = isCleanFurigana
        self.isFuriganaFilter = isFuriganaFilter