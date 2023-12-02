import os
import shutil
from PIL import Image
from numpy.lib.function_base import append
import hashlib
from segmentation import TextSegmenation
from detection import TextDetection
from ocr import TextOcr
from classes import PrintLog, Page, Chapter, Cover
from termcolor import colored
from banco.bdUtil import saveData
from furigana import RemoveFurigana
from util import printLog
import re
from unidecode import unidecode
import globals 
import shutil


def getDirectoryName(directory):
    folder = os.path.basename(directory)  # Obtem o name da folder

    if (folder.lower() == 'c:/') or (folder.lower() == 'c:\\') or ("$recycle.bin" in folder.lower()):
        return ""

    if ("[JPN]" in folder.upper()) or ("[JAP]" in folder.upper()) or ("[JNP]" in folder.upper()):
        folder = folder.replace("[JPN]", "").replace("[JAP]", "").replace("[JNP]", "")
    elif "[" in folder:
        scan = folder[folder.index("["):folder.index("]")]
        folder = folder.replace(scan, "").replace("[", "").replace("]", "")

    folder = folder.replace(" - ", " ")

    if ("volume" in folder.lower()):
        folder = folder[:folder.lower().rindex("volume")]
    elif ("capítulo" in folder.lower()):
        folder = folder[:folder.lower().rindex("capítulo")]
    elif ("capitulo" in folder.lower()):
        folder = folder[:folder.lower().rindex("capitulo")]

    return folder.replace("  ", " ").strip()


def getDirectoryInformation(directory, nameManga, language="PT"):
    folder = os.path.basename(directory)  # Pasta que está

    scan = ""
    isScan = False
    if ("[" in folder):
        if ("[JPN]" not in folder.upper()) and ("[JNP]" not in folder.upper()) and ("[JAP]" not in folder.upper()):
            scan = folder[folder.index("["):folder.index("]")]
            scan = scan.replace("[", "").replace("]", "").strip()
            isScan = bool(scan)  # Caso a scan seja vazia será falso

    folder = folder.lower()

    volume = '0'
    chapter = '0'
    isExtra = False
    if ("volume" in folder) and (("capítulo" in folder) or ("capitulo" in folder) or (("extra" in folder) and (folder.rindex("volume") < folder.rindex("extra")))):
        if "capítulo" in folder:
            volume = folder[folder.rindex("volume"):folder.rindex("capítulo")]
            volume = volume.replace("volume", "").replace("-", "").strip()

            chapter = folder[folder.rindex("capítulo"):]
            chapter = chapter.replace("capítulo", "").strip()
        elif "capitulo" in folder:
            volume = folder[folder.rindex("volume"):folder.rindex("capitulo")]
            volume = volume.replace("volume", "").replace("-", "").strip()

            chapter = folder[folder.rindex("capitulo"):]
            chapter = chapter.replace("capitulo", "").strip()
        elif "extra" in folder:
            volume = folder[folder.rindex("volume"):folder.rindex("extra")]
            volume = volume.replace("volume", "").replace("-", "").strip()

            chapter = folder[folder.rindex("extra"):]
            chapter = chapter.replace("extra", "").strip()
            isExtra = True

        volume = re.sub(r'[^0-9.]', '', volume)
        chapter = re.sub(r'[^0-9.]', '', chapter)

        if volume == "":
            volume = '0'

        if chapter == "":
            chapter = '0'

    obj = Chapter(nameManga, volume, chapter, language)
    obj.scan = scan
    obj.isScan = isScan
    obj.isExtra = isExtra

    return obj


def moveFilesDirectories(operation, diretorioOrigem, diretorioDestino, folderName):
    volume = "0"
    chapter = "0"
    i = 0
    if not operation.isTest:
        for directory, subFolder, files in os.walk(diretorioOrigem):
            operation.window.write_event_value('-THREAD_PROGRESSBAR_MAX-', len(subFolder))
            break

    for directory, subFolder, files in os.walk(diretorioOrigem):
        if len(files) == 0:
            continue

        i += 1
        if not operation.isTest:
            operation.window.write_event_value('-THREAD_PROGRESSBAR_UPDATE-', i)

        for file in files:
            name = os.path.basename(file).lower()

            try:
                if '_v' in name:
                    volume = name[name.index('_v') + 1:]
                    volume = volume[:volume.index('_')].replace("_", "")
                elif '-v' in name:
                    volume = name[name.index('-v') + 1:]
                    volume = volume[:volume.index('-')].replace("-", "")
                elif '(v' in name:
                    volume = name[name.index('(v') + 1:]
                    volume = volume[:volume.index(')')].replace("(", "").replace(")", "")
                elif re.search(" v\w+", name):
                    test = re.findall("v\w+", name)[0].replace("v", "")
                    if(test.isnumeric()):
                        volume = test

                if ('_ch' in name) or ('_c' in name):
                    chapter = name[name.index('_c') + 1:]
                    chapter = chapter[:chapter.index('_')].replace("_", "")
                elif ('-ch' in name) or ('-c' in name):
                    chapter = name[name.index('-c') + 1:]
                    chapter = chapter[:chapter.index('-')].replace("-", "")
                elif ('- c' in name):
                    chapter = name[name.index('- c') + 1:]
                    chapter = chapter[:chapter.index('(')].replace("-", "")
                elif re.search(" c\w+", name):
                    test = re.findall("c\w+", name)[0].replace("c", "")
                    if(test.isnumeric()):
                        chapter = test
                        

                volume = re.sub(r'[^0-9]', '', volume)
                chapter = re.sub(r'[^0-9]', '', chapter)
                folder = diretorioDestino + '/' + (folderName + ' - Volume ' + volume + ' Capitulo ' +  chapter)
                folder = folder.strip()
            except Exception as e:
                print(e)
                folder = diretorioDestino + "/naoreconhecidos/"

            if not os.path.exists(folder):
                os.makedirs(folder)

            fromFile = os.path.join(directory, file)
            toFile = os.path.join(folder).strip()

            shutil.copy2(fromFile, toFile)

            if not operation.isTest:
                operation.window.write_event_value('-THREAD_LOG-', PrintLog("Copiando file " + file + " para: " + toFile))
            else:
                printLog(PrintLog("Copiando file " + file + " para: " + toFile, logMemo=operation.logMemo))

            if globals.CANCEL_OPERATION:
                break

        if globals.CANCEL_OPERATION:
            break


class ImageProcess:
    def __init__(self, operation):
        pass

        # Caminhos temporários
        self.operation = operation
        self.language = operation.language
        self.nameManga = operation.nameManga
        self.folder = ''.join(operation.directory + "/").replace("//", "/")
        self.tempFolder = self.folder + "tmp/"
        self.textOnlyFolder = self.tempFolder+"textOnly/"
        self.inpaintedFolder = self.tempFolder+"inpainted/"
        self.furiganaFolder  = self.tempFolder+"furigana/"
        # self.transalatedFolder=self.tempFolder+"translated/"

    def cleanDirectories(self):
        for filePath in [self.textOnlyFolder, self.inpaintedFolder, self.furiganaFolder]:
            if os.path.exists(filePath):
                shutil.rmtree(filePath)
            os.makedirs(filePath)

    def createClassPage(self, directory, file, number):
        page = Page(file, number)
        page.file = os.path.join(directory, file)
        md5hash = hashlib.md5()
        with open(os.path.join(directory, file),'rb') as f:
          line = f.read()
          md5hash.update(line)
        page.hashPage = md5hash.hexdigest()
        return page

    def createClassChapter(self, directory, file):
        chapter = None
        if self.operation.getFolderInformation:
            chapter = getDirectoryInformation(directory, self.nameManga, self.language)
        else:
            chapter = Chapter(self.nameManga, self.operation.volume, self.operation.chapter, self.language)
            chapter.scan = self.operation.scan
            chapter.isScan = bool(chapter.scan)
        
        return chapter
    
    def createClassCover(self, directory, file):
        cover = directory + "/capa.jpg"
        with Image.open(directory + '/' + file) as im:
            oldSize = im.size
            im.thumbnail((616, 616))
            cv = im.convert('RGB')
            cv.save(cover)

            if not self.operation.isTest:
                self.operation.window.write_event_value('-THREAD_LOG-', PrintLog("Resize imagem capa: " + file + " -- " + str(oldSize) + " -> " + str(im.size), 'yellow'))
            else:
                print(colored("Resize imagem capa: " + file + " -- " + str(oldSize) + " -> " + str(im.size), 'yellow', attrs=['reverse', 'blink']))

        name, extension = os.path.splitext(cover)
        extension = extension.replace(".", "")
        return Cover(self.nameManga, self.operation.volume, self.language, name, extension, cover)

    def processImages(self):
        segmentation = TextSegmenation(self.operation)
        detection = TextDetection(0.025)
        ocr = TextOcr(self.operation)
        furigana = RemoveFurigana(self.operation)

        i = 0
        if not self.operation.isTest:
            self.operation.window.write_event_value('-THREAD_LOG-', PrintLog("Iniciado o processamento...."))
            self.operation.window.write_event_value('-THREAD_PROGRESSBAR_MAX-', len([f for f in os.listdir(self.folder) if "capa" not in f.lower() and f not in ['tmp']]))
        elif self.operation.isSilent:
            printLog(PrintLog("Iniciado o processamento....", directory=self.operation.applicationPath, isSilent=self.operation.isSilent))
        else:
            print("Iniciado o processamento....")


        images_extensions = ('.png', '.jpg', '.jpeg')
        for directory, subFolder, files in os.walk(self.folder):
            # Ignora as pastas temporárias da busca
            subFolder[:] = [sub for sub in subFolder if sub not in ['tmp']]
            # Ignora as pastas de capa
            subFolder[:] = [sub for sub in subFolder if "capa" not in sub.lower()]

            for file in files:
                if file.lower().endswith(images_extensions):
                    os.rename(os.path.join(directory, file), os.path.join(directory, unidecode(file)))

        
        cover = None

        for directory, subFolder, files in os.walk(self.folder):
            # Ignora as pastas temporárias da busca
            subFolder[:] = [sub for sub in subFolder if sub not in ['tmp']]

            # Faz a limpeza da folder temporaria para que files com o mesmo name não impactem
            self.cleanDirectories()
            if self.operation.getNameFolder:
                self.nameManga = getDirectoryName(directory)
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog("Nome obtido: " + self.nameManga, 'yellow'))
                else:
                    print(colored("Nome obtido: " + self.nameManga, 'yellow', attrs=['reverse', 'blink']))

            if len(files) <= 0:
                continue

            if "capa" in directory.lower():
                for file in files:
                    if "frente." in file.lower():
                        cover = self.createClassCover(directory, file)
                        break

                continue

            i += 1
            pageNumber = 0
            chapter = self.createClassChapter(directory, files[0])
            for file in files:
                if file.lower().endswith(images_extensions):
                    pageNumber += 1

                    log = os.path.join(directory, file)
                    # Caminho completo
                    if not self.operation.isTest:
                        self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(log, 'green'))
                    elif self.operation.isSilent:
                        printLog(PrintLog(log, 'green', directory=self.operation.applicationPath, isSilent=self.operation.isSilent))
                    else:
                        print(colored(log, 'green', attrs=['reverse', 'blink']))

                    page = self.createClassPage(directory, file, pageNumber)

                    segmentation.segmentPage(os.path.join(directory, file), self.inpaintedFolder, self.textOnlyFolder)

                    if self.operation.furigana:
                        imgGray, imgClean, imgSegment = segmentation.segmentFurigana(os.path.join(self.textOnlyFolder,file), self.furiganaFolder)
                        furigana.removeFurigana(os.path.join(self.textOnlyFolder,file), imgGray, imgClean, imgSegment, self.textOnlyFolder, self.furiganaFolder)

                    coordinates = detection.textDetect(os.path.join(directory, file), self.textOnlyFolder)
                    nomeImgNotProcess = chapter.language.upper() + '_No-' + re.sub(r'[^a-zA-Z0-9]', '',chapter.name).replace("_", "").lower().strip() + '_Vol-' + chapter.volume + '_Cap-' + chapter.chapter + '_Pag-' + str(pageNumber)
                    page.texts = ocr.getTextFromImg(os.path.join(directory, file), coordinates, self.textOnlyFolder, self.furiganaFolder, nomeImgNotProcess)
                    page.number = pageNumber
                    chapter.addPagina(page)

                if globals.CANCEL_OPERATION:
                    break

            if globals.CANCEL_OPERATION:
                break

            if len(chapter.pages) > 0:
                saveData(self.operation, chapter, cover)

            if not self.operation.isTest:
                self.operation.window.write_event_value('-THREAD_PROGRESSBAR_UPDATE-', i)

