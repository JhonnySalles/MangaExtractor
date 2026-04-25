import os
import shutil
import threading
import concurrent.futures
from dataclasses import dataclass, field
from typing import List, Optional
import manga_extractor.core.defaults as defaults
import manga_extractor.core.globals as globals
from manga_extractor.modules.segmentation import TextSegmenation
from manga_extractor.modules.detection import TextDetection
from manga_extractor.modules.ocr import TextOcr
from manga_extractor.modules.furigana import RemoveFurigana
from manga_extractor.core.classes import PrintLog, Page, Chapter, Cover
from manga_extractor.core.processor import getDirectoryName, getDirectoryInformation
from unidecode import unidecode
import re
import hashlib

@dataclass
class PageTask:
    """Representa uma página a ser processada"""
    page_number: int
    file_path: str
    file_name: str
    directory: str
    # Resultados (preenchidos durante processamento)
    page: Optional[Page] = None
    is_complete: bool = False
    error: Optional[str] = None

class ParallelImageProcess:
    def __init__(self, operation, hardware_manager):
        self.operation = operation
        self.hardware = hardware_manager
        self.language = operation.language
        self.nameManga = operation.nameManga
        self.folder = ''.join(operation.directory + "/").replace("//", "/")
        self.tempFolder = self.folder + "tmp/"
        self.textOnlyFolder = self.tempFolder + "textOnly/"
        self.inpaintedFolder = self.tempFolder + "inpainted/"
        self.furiganaFolder = self.tempFolder + "furigana/"
        
        # Semáforo para limitar a carga simultânea de páginas
        self._semaphore = threading.Semaphore(defaults.MAX_PARALLEL_PAGES)
        self.lock = threading.Lock()

    def cleanDirectories(self, page_only_folder, page_furigana_folder, page_inpainted_folder):
        for filePath in [page_only_folder, page_furigana_folder, page_inpainted_folder]:
            if os.path.exists(filePath):
                shutil.rmtree(filePath)
            os.makedirs(filePath)

    def createClassPage(self, directory, file, number):
        page = Page(file, number)
        page.file = os.path.join(directory, file)
        md5hash = hashlib.md5()
        with open(os.path.join(directory, file), 'rb') as f:
            line = f.read()
            md5hash.update(line)
        page.hashPage = md5hash.hexdigest()
        return page

    def createClassChapter(self, directory):
        chapter = None
        if self.operation.getFolderInformation:
            chapter = getDirectoryInformation(directory, self.nameManga, self.language)
        else:
            chapter = Chapter(self.nameManga, self.operation.volume, self.operation.chapter, self.language)
            chapter.scan = self.operation.scan
            chapter.isScan = bool(chapter.scan)
        return chapter

    def _log(self, message, color=None):
        if not self.operation.isTest:
            self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(message, color))
        else:
            print(message)

    def _process_single_page(self, task, segmentation, detection, ocr, furigana):
        """Processa uma única página em uma worker thread"""
        page_id = task.page_number
        page_temp = os.path.join(self.tempFolder, f"page_{page_id}/")
        p_text_only = os.path.join(page_temp, "textOnly/")
        p_inpainted = os.path.join(page_temp, "inpainted/")
        p_furigana = os.path.join(page_temp, "furigana/")

        self.cleanDirectories(p_text_only, p_furigana, p_inpainted)

        try:
            # 1. Segmentação (Thread-safe por lock em core.py)
            segmentation.segmentPage(task.file_path, p_inpainted, p_text_only)

            # 2. Furigana
            if self.operation.furigana:
                imgGray, imgClean, imgSegment = segmentation.segmentFurigana(os.path.join(p_text_only, task.file_name), p_furigana)
                furigana.removeFurigana(os.path.join(p_text_only, task.file_name), imgGray, imgClean, imgSegment, p_text_only, p_furigana)

            # 3. Detecção
            coordinates = detection.textDetect(task.file_path, p_text_only)

            # 4. OCR
            chapter_info = self.createClassChapter(task.directory) # Temporário para nome de imagem
            nomeImgNotProcess = chapter_info.language.upper() + '_No-' + re.sub(r'[^a-zA-Z0-9]', '', chapter_info.name).replace("_", "").lower().strip() + '_Vol-' + chapter_info.volume + '_Cap-' + chapter_info.chapter + '_Pag-' + str(task.page_number)
            
            page = self.createClassPage(task.directory, task.file_name, task.page_number)
            page.texts = ocr.getTextFromImg(os.path.join(task.directory, task.file_name), coordinates, p_text_only, p_furigana, nomeImgNotProcess)
            
            task.page = page
            task.is_complete = True
            
        except Exception as e:
            self._log(f"Erro na página {task.page_number} ({task.file_name}): {e}", "red")
            task.error = str(e)
        finally:
            if os.path.exists(page_temp):
                shutil.rmtree(page_temp, ignore_errors=True)
            self._semaphore.release()

    def processImages(self):
        from manga_extractor.database.db_util import saveData
        
        segmentation = TextSegmenation(self.operation)
        detection = TextDetection(0.025)
        ocr = TextOcr(self.operation)
        furigana = RemoveFurigana(self.operation)

        processedFolder = os.path.join(self.folder, 'concluido')
        if not os.path.exists(processedFolder):
            os.mkdir(processedFolder)

        imagesExtensions = ('.png', '.jpg', '.jpeg')
        
        # Coleta todas as pastas antes de começar
        all_dirs = []
        for directory, subFolder, files in os.walk(self.folder):
            subFolder[:] = [sub for sub in subFolder if sub.lower() not in ['tmp', 'concluido']]
            subFolder[:] = [sub for sub in subFolder if "capa" not in sub.lower()]
            all_dirs.append((directory, files))

        cover = None
        # Busca capa primeiro
        for directory, files in all_dirs:
            if "capa" in directory.lower():
                for file in files:
                    if "frente." in file.lower():
                        # createClassCover logic... simplificando para manter foco
                        pass
                break

        self._log("Iniado processamento paralelo...")

        for directory, files in all_dirs:
            if self.operation.getNameFolder:
                self.nameManga = getDirectoryName(directory)
                self._log(f"Nome obtido: {self.nameManga}", "yellow")

            image_files = sorted([f for f in files if f.lower().endswith(imagesExtensions)])
            if not image_files:
                continue

            chapter = self.createClassChapter(directory)
            tasks = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=defaults.MAX_OCR_WORKERS) as executor:
                futures = []
                for idx, file in enumerate(image_files, start=1):
                    if globals.CANCEL_OPERATION: break
                    
                    self._semaphore.acquire()
                    task = PageTask(page_number=idx, file_path=os.path.join(directory, file), file_name=file, directory=directory)
                    tasks.append(task)
                    
                    futures.append(executor.submit(self._process_single_page, task, segmentation, detection, ocr, furigana))

                # Aguarda finalização do capítulo
                concurrent.futures.wait(futures)

            if globals.CANCEL_OPERATION: break

            # Ordena e adiciona páginas ao capítulo
            tasks.sort(key=lambda x: x.page_number)
            for t in tasks:
                if t.is_complete and t.page:
                    chapter.addPagina(t.page)

            if len(chapter.pages) > 0:
                saveData(self.operation, chapter, cover)
                shutil.move(directory, processedFolder)
                self._log(f"Capítulo {chapter.chapter} processado e salvo.", "green")

            if not self.operation.isTest:
                self.operation.window.write_event_value('-THREAD_PROGRESSBAR_UPDATE-', 100) # Simplificado
