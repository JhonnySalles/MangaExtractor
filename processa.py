import os
import shutil
from PIL import Image
from numpy.lib.function_base import append
import hashlib
from segmentacao import TextSegmenation
from detecao import TextDetection
from ocr import TextOcr
from classes import Manga
from termcolor import colored

class ImageProcess:
    def __init__(self, operacao):
        pass

        # Caminhos temporários
        self.operacao = operacao
        self.language = operacao.linguagem
        self.manga = operacao.manga
        self.folder = ''.join(operacao.caminho + "/").replace("//","/")
        self.tempFolder = self.folder + "tmp/"
        self.textOnlyFolder=self.tempFolder+"textOnly/"
        self.inpaintedFolder=self.tempFolder+"inpainted/"
        self.transalatedFolder=self.tempFolder+"translated/"
    
    def criaDiretorios(self):
        for filePath in [self.textOnlyFolder, self.inpaintedFolder, self.transalatedFolder]:
            if not os.path.exists(filePath):
                os.makedirs(filePath)
            else:
                shutil.rmtree(filePath)
                os.makedirs(filePath)

    def limpaDiretorios(self):
        for filePath in [self.textOnlyFolder, self.inpaintedFolder, self.transalatedFolder]:
            if os.path.exists(filePath):
                shutil.rmtree(filePath)
            os.makedirs(filePath)

    def extraiInformacoesDiretorio(self, diretorio):
        pasta = os.path.basename(diretorio) # Pasta que está

        if "[" in pasta:
            scan = pasta[pasta.index("["):pasta.index("]")]
            scan = scan.replace("[","").replace("]","").strip()
            isScan = bool(scan) # Caso a scan seja vazia será falso
        else:
            scan = ""
            isScan = bool("FALSE")

        pasta = pasta.lower()
        volume = pasta[pasta.index("volume"):pasta.index("-", pasta.index("volume"))]
        volume = volume.replace("volume", "").strip()

        if "capítulo" in pasta:
            capitulo = pasta[pasta.index("capítulo"):]
            capitulo = capitulo.replace("capítulo", "").strip()
        else:
            capitulo = pasta[pasta.index("capitulo"):]
            capitulo = capitulo.replace("capitulo", "").strip()

        manga = Manga(self.manga, volume, capitulo)
        manga.scan = scan
        manga.isScan = isScan

        return manga

    def criaClasseManga(self, diretorio, arquivo):
        manga = None
        if self.operacao.isFolder:
            manga = self.extraiInformacoesDiretorio(diretorio)
        else:
            manga = Manga(self.operacao.manga, self.operacao.volume, self.operacao.capitulo)
            manga.scan = self.operacao.scan
            manga.isScan = bool(manga.scan.strip() == "")

        manga.nomePagina = arquivo
        manga.arquivo = os.path.join(diretorio, arquivo)
        md5hash = hashlib.md5(Image.open(os.path.join(diretorio, arquivo)).tobytes())
        manga.hashPagina = md5hash.hexdigest()
        return manga
                
    def processaImagens(self):
        self.criaDiretorios
        processados = []

        segmentacao = TextSegmenation()
        deteccao = TextDetection(0.025)
        ocr = TextOcr(self.operacao)
        
        print("Iniciado o processamento....")
        self.operacao.window['-OUTPUT-'].print("Iniciado o processamento....")

        for diretorio, subpastas, arquivos in os.walk(self.folder):
            if "tmp" in subpastas: #Ignora as pastas temporárias da busca
                subpastas.remove("tmp")
                continue
            pagina = 0
            for arquivo in arquivos:
                if arquivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                    pagina += 1

                    log = os.path.join(diretorio, arquivo)

                    print(colored(log, 'green', attrs=['reverse', 'blink'])) # Caminho completo
                    self.operacao.window['-OUTPUT-'].print(log, text_color='cyan')

                    manga = self.criaClasseManga(diretorio, arquivo)

                    segmentacao.segmentPage(os.path.join(diretorio, arquivo),self.inpaintedFolder,self.textOnlyFolder)
                    coordenadas = deteccao.textDetect(os.path.join(diretorio, arquivo),self.textOnlyFolder)
                    manga.textos = ocr.getTextFromImg(os.path.join(diretorio, arquivo),coordenadas,self.textOnlyFolder)
                    manga.numeroPagina = pagina
                    manga.linguagem = self.language
                    processados.append(manga)

            #Faz a limpeza para que arquivos com o mesmo nome não impactem
            self.limpaDiretorios()

        return processados                           
