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

    def addTexto(self, texto):
        self.textos.append(texto)

class Operacao:
    def __init__(self, window, manga, caminho, linguagem):
        pass
        
        self.manga = manga
        self.caminho = caminho.replace('\\','/')
        self.linguagem = linguagem.lower()
        self.volume = None
        self.capitulo = None
        self.scan = None
        self.base = manga
        self.isFolder = True
        self.ocrType = "winocr"
        self.window = window
        self.pastaTesseract = "C:/Program Files/Tesseract-OCR"
        self.isTeste = False
