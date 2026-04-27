import os
import cv2
import re
import subprocess
import threading
from manga_extractor.core.classes import Text, PrintLog
from PIL import Image
import pytesseract
from manga_extractor.core.defaults import FOLDER_SAVE_IMAGE_NOT_LOCATED_TEXT


class TextOcr():
    def __init__(self, operation):
        self.operation = operation
        self.ocrType = operation.ocrType
        self.language = operation.language
        self.tesseractLocation = ''.join(operation.tesseractFolder + '/tesseract.exe').replace('//', '/')
        self.tesseractConfig = None

        if (self.language == 'ja'):
            if (self.operation.verticalText is None):
                self.tesseractConfig = r' -l jpn+jpn_vert '
            elif (self.operation.verticalText):
                self.tesseractConfig = r' -l jpn_vert '
            elif (not self.operation.verticalText):
                self.tesseractConfig = r' -l jpn '
        elif (self.language == 'en'):
            self.tesseractConfig = r' -l eng '
        elif (self.language == 'pt'):
            self.tesseractConfig = r' -l por '


    def filterText(self, inputText):
        if (self.language == "ja"):
            caracteres = r'[\\+/§◎*)@<>#%(&=$_\-^01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz:;«¢~「」〃ゝゞヽヾ一●▲・ヽ÷①↓®▽■◆『£〆∴∞▼™↑←]'
        else:
            caracteres = r'[\\+/§◎*)@<>#%(&=$_\-^«¢~「」〃ゝゞヽヾ一●▲・ヽ÷①↓®▽■◆『£〆∴∞▼™↑←]'


        inputText = re.sub(caracteres, '', inputText)  # remove special cha

        if (self.language == "ja"):
            inputText = ''.join(inputText.split())  # remove whitespace
        else:
            inputText = ' '.join(inputText.split())  # remove whitespace
            inputText = inputText.capitalize()  # Letras minuscula com a primeira maiuscula

        return inputText


    def getTextWindowOcr(self, img):
        thread_id = threading.current_thread().ident
        inputFile = f"lib/input_{thread_id}.jpg"
        outputFile = f'lib/output_{thread_id}.txt'
        cv2.imwrite(inputFile, img)
        p = subprocess.Popen(('./lib/winocr/winocr.exe'))
        p.wait()
        try:
            with open(outputFile, "r", encoding="utf-8") as f:
                text = f.read()  # txt to str
        except UnicodeDecodeError:
            with open(outputFile, "r", encoding="latin-1") as f:
                text = f.read()
        if os.path.exists(inputFile):
            os.remove(inputFile)
        if os.path.exists(outputFile):
            os.remove(outputFile)
        text = self.filterText(text)
        return text

    def checkWindowOcr(self,):
        p = subprocess.Popen(('./lib/winocr/winocr.exe'))
        p.wait()
        if os.path.exists("./lib/loadResult.txt"):
            try:
                with open("./lib/loadResult.txt", "r", encoding="utf-8") as f:
                    text = f.read()  # txt to str
            except UnicodeDecodeError:
                with open("./lib/loadResult.txt", "r", encoding="latin-1") as f:
                    text = f.read()
            if text == "True":
                return True
        return False

    def getTextTesseractOcr(self, img, folder):
        thread_id = threading.current_thread().ident
        inputFile = folder + f"input_{thread_id}.jpg"
        cv2.imwrite(inputFile, img)
        pytesseract.pytesseract.tesseract_cmd = self.tesseractLocation

        if (self.tesseractConfig is not None):
            text = pytesseract.image_to_string(Image.open(inputFile), config=self.tesseractConfig)
        else:
            text = pytesseract.image_to_string(Image.open(inputFile))
        
        if os.path.exists(inputFile):
            os.remove(inputFile)

        text = self.filterText(text)
        return text

    def getText(self, cropped, folder):
        text = ""
        if self.ocrType == "winocr":
            text = self.getTextWindowOcr(cropped)
        elif self.ocrType == "tesseract":
            text = self.getTextTesseractOcr(cropped, folder)
        
        return text


    def saveNotProcess(self, cropped, name):
        nomeImgNotProcess = FOLDER_SAVE_IMAGE_NOT_LOCATED_TEXT + '/' + name + '.jpg'
        cv2.imwrite(nomeImgNotProcess, cropped)


    def getTextFromImg(self, imgPath, rectList, textOnlyFolder, furiganaFolder, nameIfNotProcess = ""):
        fileName = os.path.basename(imgPath)
        if self.operation.furigana:
            folder = furiganaFolder
        else:
            folder = textOnlyFolder

        saveImgNotProcess = (FOLDER_SAVE_IMAGE_NOT_LOCATED_TEXT != "") and (os.path.exists(FOLDER_SAVE_IMAGE_NOT_LOCATED_TEXT)) and (nameIfNotProcess != "")

        img = cv2.imread(folder+fileName)
        imgWrite = cv2.imread(folder+fileName)
        texts = []
        rectP, rect = rectList
        sequence = 0
        for x1, y1, x2, y2 in rectP:
            # Cropping the text block for giving input to OCR
            cropped = img[y1: y2, x1: x2]

            text = self.getText(cropped, folder)

            if text.strip() != "":
                log = "  • " + text
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(log)) 
                else:
                    print(log)

                texts.append(Text(text, sequence, x1, y1, x2, y2))
                sequence += 1
                cv2.rectangle(imgWrite, (x1, y1), (x2, y2), (0, 255, 0))
            elif self.operation.furigana:
                folder = textOnlyFolder
                img2 = cv2.imread(folder+fileName)
                # Cropping the text block for giving input to OCR
                cropped = img2[y1: y2, x1: x2]
                text = self.getText(cropped, folder)

                if text.strip() != "":
                    log = "  • " + text
                    if not self.operation.isTest:
                        self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(log)) 
                    else:
                        print(log)

                    texts.append(Text(text, sequence, x1, y1, x2, y2))
                    sequence += 1
                    cv2.rectangle(imgWrite, (x1, y1), (x2, y2), (0, 255, 0))
                else:
                    cv2.rectangle(imgWrite, (x1, y1), (x2, y2), (0, 0, 255)) # Caso não conseguiu identificar o text pinta de vermelho
                    if saveImgNotProcess:
                        self.saveNotProcess(cropped, nameIfNotProcess + '_Seq-' + str(sequence) + '_Pos-' + str(x1) + '-' + str(y1) + '-' + str(x2) + '-' + str(y2) + '_')

            else:
                cv2.rectangle(imgWrite, (x1, y1), (x2, y2), (0, 0, 255)) # Caso não conseguiu identificar o text pinta de vermelho
                if saveImgNotProcess:
                    self.saveNotProcess(cropped, nameIfNotProcess + '_Seq-' + str(sequence) + '_Pos-' + str(x1) + '-' + str(y1) + '-' + str(x2) + '-' + str(y2) + '_')
                      
        cv2.imwrite(folder+fileName, imgWrite)
        return texts
