class Texto:
     def __init__(self, texto, sequencia, posX1, posY1, posX2, posY2):
        pass
        self.texto = texto
        self.sequencia = sequencia
        self.posX1 = posX1
        self.posY1 = posY1
        self.posX2 = posX2
        self.posY2 = posY2

class Manga:
    def __init__(self, nome, volume, capitulo):
        pass
        
        self.nome = nome
        self.volume = volume
        self.capitulo = capitulo
        self.arquivo = ""
        self.nomePagina = ""
        self.numeroPagina = 0
        self.linguagem = ""
        self.textos = []
        self.hashPagina = ""
        self.scan = ""
        self.isScan = False
        self.isExtra = False

    def addTexto(self, texto):
        self.textos.append(texto)

class Operacao:
    def __init__(self, window, base, mangaNome, caminho, linguagem):
        pass
        
        self.mangaNome = mangaNome
        self.caminho = caminho.replace('\\','/')
        self.linguagem = linguagem.lower()
        self.textoVertical = None
        self.volume = None
        self.capitulo = None
        self.scan = None
        self.base = base
        self.getInformacaoPasta = True
        self.getNomePasta = False
        self.ocrType = "winocr"
        self.pastaTesseract = "C:/Program Files/Tesseract-OCR"
        self.isTeste = window is None
        self.window = window

        if not self.isTeste:
            self.logMemo = window['-OUTPUT-']
            self.progress = window['progressbar']

