import os
import shutil
from PIL import Image
from numpy.lib.function_base import append
import hashlib
from segmentacao import TextSegmenation
from detecao import TextDetection
from ocr import TextOcr
from classes import PrintLog, Pagina, Capitulo
from termcolor import colored
from banco.bdUtil import gravarDados
from furigana import RemoveFurigana
from util import printLog
import re
from unidecode import unidecode


def extraiNomeDiretorio(diretorio):
    pasta = os.path.basename(diretorio)  # Obtem o nome da pasta

    if ("[JPN]" in pasta.upper()) or ("[JAP]" in pasta.upper()) or ("[JNP]" in pasta.upper()):
        pasta = pasta.replace("[JPN]", "").replace("[JAP]", "").replace("[JNP]", "")
    elif "[" in pasta:
        scan = pasta[pasta.index("["):pasta.index("]")]
        pasta = pasta.replace(scan, "").replace("[", "").replace("]", "")

    pasta = pasta.replace(" - ", " ")

    if ("volume" in pasta.lower()):
        pasta = pasta[:pasta.lower().rindex("volume")]
    elif ("capítulo" in pasta.lower()):
        pasta = pasta[:pasta.lower().rindex("capítulo")]
    elif ("capitulo" in pasta.lower()):
        pasta = pasta[:pasta.lower().rindex("capitulo")]

    return pasta.replace("  ", " ").strip()


def extraiInformacoesDiretorio(diretorio, mangaNome, language="PT"):
        pasta = os.path.basename(diretorio)  # Pasta que está

        scan = ""
        isScan = False
        if ("[" in pasta):
            if ("[JPN]" not in pasta.upper()) and ("[JNP]" not in pasta.upper()) and ("[JAP]" not in pasta.upper()):
                scan = pasta[pasta.index("["):pasta.index("]")]
                scan = scan.replace("[", "").replace("]", "").strip()
                isScan = bool(scan)  # Caso a scan seja vazia será falso

        pasta = pasta.lower()

        volume = '0'
        capitulo = '0'
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

            volume = re.sub(r'[^0-9.]', '', volume)
            capitulo = re.sub(r'[^0-9.]', '', capitulo)

            if volume == "":
                volume = '0'

            if capitulo == "":
                capitulo = '0'

        obj = Capitulo(mangaNome, volume, capitulo, language)
        obj.scan = scan
        obj.isScan = isScan
        obj.isExtra = isExtra

        return obj


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

    def criaClassePagina(self, diretorio, arquivo, numero):
        pagina = Pagina(arquivo, numero)
        pagina.arquivo = os.path.join(diretorio, arquivo)
        md5hash = hashlib.md5(Image.open(os.path.join(diretorio, arquivo)).tobytes())
        pagina.hashPagina = md5hash.hexdigest()
        return pagina

    def criaClasseCapitulo(self, diretorio, arquivo):
        capitulo = None
        if self.operacao.getInformacaoPasta:
            capitulo = extraiInformacoesDiretorio(diretorio, self.mangaNome, self.language)
        else:
            capitulo = Capitulo(self.mangaNome, self.operacao.volume, self.operacao.capitulo, self.language)
            capitulo.scan = self.operacao.scan
            capitulo.isScan = bool(capitulo.scan)
        
        return capitulo

    def processaImagens(self):
        segmentacao = TextSegmenation(self.operacao)
        deteccao = TextDetection(0.025)
        ocr = TextOcr(self.operacao)
        furigana = RemoveFurigana(self.operacao)

        i = 0
        if not self.operacao.isTeste:
            self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog("Iniciado o processamento...."))
            self.operacao.window.write_event_value('-THREAD_PROGRESSBAR_MAX-', len([f for f in os.listdir(self.folder) if "capa" not in f.lower() and f not in ['tmp']]))
        elif self.operacao.isSilent:
            printLog(PrintLog("Iniciado o processamento....", caminho=self.operacao.caminhoAplicacao, isSilent=self.operacao.isSilent))
        else:
            print("Iniciado o processamento....")


        IMAGENS_EXTENSOES = ('.png', '.jpg', '.jpeg')
        for diretorio, subpastas, arquivos in os.walk(self.folder):
            # Ignora as pastas temporárias da busca
            subpastas[:] = [sub for sub in subpastas if sub not in ['tmp']]
            # Ignora as pastas de capa
            subpastas[:] = [sub for sub in subpastas if "capa" not in sub.lower()]

            for arquivo in arquivos:
                if arquivo.lower().endswith(IMAGENS_EXTENSOES):
                    os.rename(os.path.join(diretorio, arquivo), os.path.join(diretorio, unidecode(arquivo)))

        for diretorio, subpastas, arquivos in os.walk(self.folder):
            # Ignora as pastas temporárias da busca
            subpastas[:] = [sub for sub in subpastas if sub not in ['tmp']]
            # Ignora as pastas de capa
            subpastas[:] = [sub for sub in subpastas if "capa" not in sub.lower()]

            # Faz a limpeza da pasta temporaria para que arquivos com o mesmo nome não impactem
            self.limpaDiretorios()
            if self.operacao.getNomePasta:
                self.mangaNome = extraiNomeDiretorio(diretorio)
                if not self.operacao.isTeste:
                    self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog("Nome obtido: " + self.mangaNome, 'yellow'))
                else:
                    print(colored("Nome obtido: " + self.mangaNome, 'yellow', attrs=['reverse', 'blink']))

            if len(arquivos) <= 0:
                continue

            i += 1
            numeroPagina = 0
            capitulo = self.criaClasseCapitulo(diretorio, arquivos[0])
            for arquivo in arquivos:
                if arquivo.lower().endswith(IMAGENS_EXTENSOES):
                    numeroPagina += 1

                    log = os.path.join(diretorio, arquivo)
                    # Caminho completo
                    if not self.operacao.isTeste:
                        self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(log, 'green'))
                    elif self.operacao.isSilent:
                        printLog(PrintLog(log, 'green', caminho=self.operacao.caminhoAplicacao, isSilent=self.operacao.isSilent))
                    else:
                        print(colored(log, 'green', attrs=['reverse', 'blink']))

                    pagina = self.criaClassePagina(diretorio, arquivo, numeroPagina)

                    segmentacao.segmentPage(os.path.join(diretorio, arquivo), self.inpaintedFolder, self.textOnlyFolder)

                    if self.operacao.furigana:
                        imgGray, imgClean, imgSegment = segmentacao.segmentFurigana(os.path.join(self.textOnlyFolder,arquivo), self.furiganaFolder)
                        furigana.removeFurigana(os.path.join(self.textOnlyFolder,arquivo), imgGray, imgClean, imgSegment, self.textOnlyFolder, self.furiganaFolder)

                    coordenadas = deteccao.textDetect(os.path.join(diretorio, arquivo), self.textOnlyFolder)
                    nomeImgNotProcess = capitulo.linguagem.upper() + '_No-' + re.sub(r'[^a-zA-Z0-9]', '',capitulo.nome).replace("_", "").lower().strip() + '_Vol-' + capitulo.volume + '_Cap-' + capitulo.capitulo + '_Pag-' + str(numeroPagina)
                    pagina.textos = ocr.getTextFromImg(os.path.join(diretorio, arquivo), coordenadas, self.textOnlyFolder, self.furiganaFolder, nomeImgNotProcess)
                    pagina.numeroPagina = numeroPagina
                    capitulo.addPagina(pagina)

            if len(capitulo.paginas) > 0:
                gravarDados(self.operacao, capitulo)

            if not self.operacao.isTeste:
                self.operacao.window.write_event_value('-THREAD_PROGRESSBAR_UPDATE-', i)

