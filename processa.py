import os
import shutil
from PIL import Image
from numpy.lib.function_base import append
import hashlib
from segmentacao import TextSegmenation
from detecao import TextDetection
from ocr import TextOcr
from classes import Manga, PrintLog
from termcolor import colored
from banco.bdUtil import gravarDados
from furigana import RemoveFurigana


def extraiNomeDiretorio(diretorio):
    pasta = os.path.basename(diretorio)  # Obtem o nome da pasta

    if ("[JPN]" in pasta.upper()) or ("[JAP]" in pasta.upper()) or ("[JNP]" in pasta.upper()):
        pasta = pasta.replace("[JPN]", "").replace("[JAP]", "").replace("[JNP]", "")
    elif "[" in pasta:
        scan = pasta[pasta.index("["):pasta.index("]")]
        pasta = pasta.replace(scan, "")

    pasta = pasta.replace(" - ", " ")

    if ("volume" in pasta.lower()):
        pasta = pasta[:pasta.lower().rindex("volume")]
    elif ("capítulo" in pasta.lower()):
        pasta = pasta[:pasta.lower().rindex("capítulo")]
    elif ("capitulo" in pasta.lower()):
        pasta = pasta[:pasta.lower().rindex("capitulo")]

    return pasta.replace("  ", " ").strip()


class ImageProcess:
    def __init__(self, operacao):
        pass

        # Caminhos temporários
        self.operacao = operacao
        self.language = operacao.linguagem
        self.mangaNome = operacao.mangaNome
        self.folder = ''.join(operacao.caminho + "/").replace("//", "/")
        self.tempFolder = self.folder + "tmp/"
        self.textOnlyFolder = self.tempFolder+"textOnly/"
        self.inpaintedFolder = self.tempFolder+"inpainted/"
        self.furiganaFolder  = self.tempFolder+"furigana/"
        # self.transalatedFolder=self.tempFolder+"translated/"

    def limpaDiretorios(self):
        for filePath in [self.textOnlyFolder, self.inpaintedFolder, self.furiganaFolder]:
            if os.path.exists(filePath):
                shutil.rmtree(filePath)
            os.makedirs(filePath)

    def extraiInformacoesDiretorio(self, diretorio):
        pasta = os.path.basename(diretorio)  # Pasta que está

        scan = ""
        isScan = False
        if ("[" in pasta):
            if ("[JPN]" not in pasta.upper()) and ("[JNP]" not in pasta.upper()) and ("[JPN]" not in pasta.upper()):
                scan = pasta[pasta.index("["):pasta.index("]")]
                scan = scan.replace("[", "").replace("]", "").strip()
                isScan = bool(scan)  # Caso a scan seja vazia será falso

        pasta = pasta.lower()

        volume = 0
        capitulo = 0
        isExtra = False
        if ("capítulo" in pasta) or ("capitulo" in pasta) or (("extra" in pasta) and (pasta.rindex("volume") < pasta.rindex("extra"))):
            if "capítulo" in pasta:
                volume = pasta[pasta.rindex("volume"):pasta.rindex("capítulo")]
                volume = volume.replace("volume", "").replace("-", "").strip()

                capitulo = pasta[pasta.rindex("capítulo"):]
                capitulo = capitulo.replace("capítulo", "").strip()
            elif "capitulo" in pasta:
                volume = pasta[pasta.rindex("volume"):pasta.rindex("capitulo")]
                volume = volume.replace("volume", "").replace("-", "").strip()

                capitulo = pasta[pasta.rindex("capitulo"):]
                capitulo = capitulo.replace("capitulo", "").strip()
            elif "extra" in pasta:
                volume = pasta[pasta.rindex("volume"):pasta.rindex("extra")]
                volume = volume.replace("volume", "").replace("-", "").strip()

                capitulo = pasta[pasta.rindex("extra"):]
                capitulo = capitulo.replace("extra", "").strip()
                isExtra = True

        manga = Manga(self.mangaNome, volume, capitulo)
        manga.scan = scan
        manga.isScan = isScan
        manga.isExtra = isExtra

        return manga

    def criaClasseManga(self, diretorio, arquivo):
        manga = None
        if self.operacao.getInformacaoPasta:
            manga = self.extraiInformacoesDiretorio(diretorio)
        else:
            manga = Manga(self.operacao.mangaNome, self.operacao.volume, self.operacao.capitulo)
            manga.scan = self.operacao.scan
            manga.isScan = bool(manga.scan)

        manga.nomePagina = arquivo
        manga.arquivo = os.path.join(diretorio, arquivo)
        md5hash = hashlib.md5(Image.open(os.path.join(diretorio, arquivo)).tobytes())
        manga.hashPagina = md5hash.hexdigest()
        return manga

    def processaImagens(self):
        segmentacao = TextSegmenation(self.operacao)
        deteccao = TextDetection(0.025)
        ocr = TextOcr(self.operacao)
        furigana = RemoveFurigana(self.operacao)

        i = 0
        if not self.operacao.isTeste:
            self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog("Iniciado o processamento...."))
            self.operacao.window.write_event_value('-THREAD_PROGRESSBAR_MAX-', len(os.listdir(self.folder)))
        else:
            print("Iniciado o processamento....")

        for diretorio, subpastas, arquivos in os.walk(self.folder):
            # Ignora as pastas temporárias da busca
            subpastas[:] = [sub for sub in subpastas if sub not in ['tmp']]
            # Ignora as pastas de capa
            subpastas[:] = [
                sub for sub in subpastas if "capa" not in sub.lower()]

            # Faz a limpeza da pasta temporaria para que arquivos com o mesmo nome não impactem
            self.limpaDiretorios()
            if self.operacao.getNomePasta:
                self.mangaNome = extraiNomeDiretorio(diretorio)
                if not self.operacao.isTeste:
                    self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog("Nome obtido: " + self.mangaNome, 'yellow'))
                else:
                    print(colored("Nome obtido: " + self.mangaNome, 'yellow', attrs=['reverse', 'blink']))

            i += 1
            pagina = 0
            processados = []
            for arquivo in arquivos:
                if arquivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                    pagina += 1

                    log = os.path.join(diretorio, arquivo)
                    # Caminho completo
                    if not self.operacao.isTeste:
                        self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(log, 'green'))
                    else:
                        print(colored(log, 'green', attrs=['reverse', 'blink']))

                    manga = self.criaClasseManga(diretorio, arquivo)

                    segmentacao.segmentPage(os.path.join(diretorio, arquivo), self.inpaintedFolder, self.textOnlyFolder)

                    if self.operacao.furigana:
                        imgGray, imgClean, imgSegment = segmentacao.segmentFurigana(os.path.join(self.textOnlyFolder,arquivo), self.furiganaFolder)
                        furigana.removeFurigana(os.path.join(self.textOnlyFolder,arquivo), imgGray, imgClean, imgSegment, self.textOnlyFolder, self.furiganaFolder)

                    coordenadas = deteccao.textDetect(os.path.join(diretorio, arquivo), self.textOnlyFolder)
                    manga.textos = ocr.getTextFromImg(os.path.join(diretorio, arquivo), coordenadas, self.textOnlyFolder, self.furiganaFolder)
                    manga.numeroPagina = pagina
                    manga.linguagem = self.language
                    processados.append(manga)

            if len(processados) > 0:
                gravarDados(self.operacao, processados)

            if not self.operacao.isTeste:
                self.operacao.window.write_event_value('-THREAD_PROGRESSBAR_UPDATE-', i)

