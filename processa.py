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
from banco.bdUtil import gravarDados
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
        #self.transalatedFolder=self.tempFolder+"translated/"

    def limpaDiretorios(self):
        for filePath in [self.textOnlyFolder, self.inpaintedFolder]:
            if os.path.exists(filePath):
                shutil.rmtree(filePath)
            os.makedirs(filePath)

    def extraiNomeDiretorio(self, diretorio):
        if not self.operacao.getNomePasta:
            return

        pasta = os.path.basename(diretorio) # Pasta que está

        if ("[JPN]" in pasta.upper()) or ("[JAP]" in pasta.upper()) or ("[JNP]" not in pasta.upper()):
            pasta = pasta.replace("[JPN]", "").replace("[JAP]", "").replace("[JNP]", "")
        elif "[" in pasta:
            scan = pasta[pasta.index("["):pasta.index("]")]
            pasta = pasta.replace(scan, "")
 
        pasta = pasta.replace(" - ", "")

        if ("capítulo" in pasta.lower()) or ("capitulo" in pasta.lower()) or ("extra" in pasta.lower()):
            if "capítulo" in pasta.lower():
                volume = pasta[pasta.lower().index("volume"):pasta.lower().index("capítulo")]
                capitulo = pasta[pasta.index("capítulo"):]
            elif "capitulo" in pasta.lower() :
                volume = pasta[pasta.lower().index("volume"):pasta.lower().index("capitulo")]
                capitulo = pasta[pasta.lower().index("capitulo"):]
            elif "extra" in pasta.lower() :
                volume = pasta[pasta.lower().index("volume"):pasta.lower().index("extra")]
                capitulo = pasta[pasta.lower().index("extra"):]

            pasta = pasta.replace(volume, "").replace(capitulo, "")

        self.manga = pasta

    def extraiInformacoesDiretorio(self, diretorio):
        pasta = os.path.basename(diretorio) # Pasta que está

        scan = ""
        isScan = False
        if ("[" in pasta):
            if ("[JPN]" not in pasta.upper()) and ("[JNP]" not in pasta.upper()) and ("[JPN]" not in pasta.upper()): 
                scan = pasta[pasta.index("["):pasta.index("]")]
                scan = scan.replace("[","").replace("]","").strip()
                isScan = bool(scan) # Caso a scan seja vazia será falso 

        pasta = pasta.lower()

        isExtra  = False
        if ("capítulo" in pasta) or ("capitulo" in pasta) or ("extra" in pasta):
            if "capítulo" in pasta :
                volume = pasta[pasta.index("volume"):pasta.index("capítulo")]
                volume = volume.replace("volume", "").replace("-", "").strip()

                capitulo = pasta[pasta.index("capítulo"):]
                capitulo = capitulo.replace("capítulo", "").strip()
            elif "capitulo" in pasta :
                volume = pasta[pasta.index("volume"):pasta.index("capitulo")]
                volume = volume.replace("volume", "").replace("-", "").strip()

                capitulo = pasta[pasta.index("capitulo"):]
                capitulo = capitulo.replace("capitulo", "").strip()
            elif "extra" in pasta :
                volume = pasta[pasta.index("volume"):pasta.index("extra")]
                volume = volume.replace("volume", "").replace("-", "").strip()

                capitulo = pasta[pasta.index("extra"):]
                capitulo = capitulo.replace("extra", "").strip()
                isExtra  = True

        manga = Manga(self.manga, volume, capitulo)
        manga.scan = scan
        manga.isScan = isScan
        manga.isExtra = isExtra

        return manga

    def criaClasseManga(self, diretorio, arquivo):
        manga = None
        if self.operacao.getInformacaoPasta:
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
        segmentacao = TextSegmenation()
        deteccao = TextDetection(0.025)
        ocr = TextOcr(self.operacao)
        
        i = 0
        print("Iniciado o processamento....")
        if not self.operacao.isTeste:
            self.operacao.logMemo.print("Iniciado o processamento....")
            self.operacao.window['progressbar'].Update(len(os.listdir(self.folder)))

        for diretorio, subpastas, arquivos in os.walk(self.folder):
            subpastas[:] = [sub for sub in subpastas if sub not in ['tmp']] #Ignora as pastas temporárias da busca
            subpastas[:] = [sub for sub in subpastas if "capa" not in sub.lower()] #Ignora as pastas de capa

            #Faz a limpeza da pasta temporaria para que arquivos com o mesmo nome não impactem
            self.limpaDiretorios()
            self.extraiNomeDiretorio(diretorio)

            i += 1
            pagina = 0
            processados = []
            for arquivo in arquivos:
                if arquivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                    pagina += 1

                    log = os.path.join(diretorio, arquivo)

                    print(colored(log, 'green', attrs=['reverse', 'blink'])) # Caminho completo
                    if not self.operacao.isTeste:
                        self.operacao.logMemo.print(log, text_color='cyan')

                    manga = self.criaClasseManga(diretorio, arquivo)

                    segmentacao.segmentPage(os.path.join(diretorio, arquivo),self.inpaintedFolder,self.textOnlyFolder)
                    coordenadas = deteccao.textDetect(os.path.join(diretorio, arquivo),self.textOnlyFolder)
                    manga.textos = ocr.getTextFromImg(os.path.join(diretorio, arquivo),coordenadas,self.textOnlyFolder)
                    manga.numeroPagina = pagina
                    manga.linguagem = self.language
                    processados.append(manga)

            if len(processados) > 0:
                gravarDados(self.operacao, processados)

            if not self.operacao.isTeste:
                self.operacao.progress.UpdateBar(i)

                           
