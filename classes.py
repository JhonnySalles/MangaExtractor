import defaults

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
    def __init__(self, nome, volume, linguagem, capitulos=[]):
        pass
        self.nome = nome
        self.volume = volume
        self.linguagem = linguagem
        self.capitulos = capitulos

    def addCapitulo(self, texto):
        self.capitulos.append(texto)


class PrintLog:
    def __init__(self, mensagem, cor=None, save=True):
        pass
        self.mensagem = mensagem
        self.cor = cor
        self.save = save


class Operacao:
    def __init__(self, base, mangaNome, caminho, linguagem, window=None, ocrType='tesseract', furigana=False):
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
        self.getNomePasta = False
        self.furigana = furigana
        self.filtroAdicional = False
        self.ocrType = ocrType
        self.pastaTesseract = defaults.DEFAULT_TESSERACT_FOLDER
        self.isTeste = window is None
        self.window = window

        if not self.isTeste:
            self.logMemo = window['-OUTPUT-']
            self.progress = window['-PROGRESSBAR-']
