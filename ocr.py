from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import io
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import os
import pickle
import cv2
import re
import subprocess
from classes import Text, PrintLog
from PIL import Image
import pytesseract
from defaults import FOLDER_SAVE_IMAGE_NOT_LOCATED_TEXT


class TextOcr():
    def __init__(self, operation):
        self.operation = operation
        self.service = None
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

    def getGoogleCred(self,):
        SCOPES = ['https://console.cloud.google.com/']
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        service = build('drive', 'v3', credentials=creds)
        return service

    def filterText(self, inputText):
        if (self.language == "ja"):
            caracteres = '[\\\\+/§◎*)@<>#%(&=$_\-^01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz:;«¢~「」〃ゝゞヽヾ一●▲・ヽ÷①↓®▽■◆『£〆∴∞▼™↑←]'
        else:
            caracteres = '[\\\\+/§◎*)@<>#%(&=$_\-^«¢~「」〃ゝゞヽヾ一●▲・ヽ÷①↓®▽■◆『£〆∴∞▼™↑←]'

        inputText = re.sub(caracteres, '', inputText)  # remove special cha

        if (self.language == "ja"):
            inputText = ''.join(inputText.split())  # remove whitespace
        else:
            inputText = ' '.join(inputText.split())  # remove whitespace
            inputText = inputText.capitalize()  # Letras minuscula com a primeira maiuscula

        return inputText

    def getTextGoogleOcr(self, img):
        if self.service is None:
            self.service = self.getGoogleCred()

        exceptionCount = 0
        while exceptionCount < 5:
            try:
                # https://tanaikech.github.io/2017/05/02/ocr-using-google-drive-api/
                txtPath = 'googleocr.txt'  # Text file outputted by OCR
                imgPath = "googleocr.jpg"
                cv2.imwrite(imgPath, img)
                mime = 'application/vnd.google-apps.document'
                res = self.service.files().create(
                    body={'name': imgPath,'mimeType': mime},
                    media_body=MediaFileUpload(imgPath, mimetype=mime, resumable=True)).execute()
                downloader = MediaIoBaseDownload(io.FileIO(txtPath, 'wb'),self.service.files().export_media(fileId=res['id'], mimeType="text/plain"))
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                self.service.files().delete(fileId=res['id']).execute()
                with open(txtPath, "r", encoding="utf-8") as f:
                    text_google = f.read()  # txt to str
                text_google = text_google.replace('\ufeff', '')
                text_google = self.filterText(text_google)
                print(text_google)
            except:
                exceptionCount += 1
                print('exception')
                continue
            break
        return text_google

    def getTextWindowOcr(self, img):
        inputFile = "lib_/input.jpg"
        outputFile = 'lib_/output.txt'
        cv2.imwrite(inputFile, img)
        p = subprocess.Popen(('./lib_/winocr/winocr.exe'))
        p.wait()
        with open(outputFile, "r", encoding="utf-8") as f:
            text = f.read()  # txt to str
        if os.path.exists(inputFile):
            os.remove(inputFile)
        if os.path.exists(outputFile):
            os.remove(outputFile)
        text = self.filterText(text)
        return text

    def checkWindowOcr(self,):
        p = subprocess.Popen(('./lib_/winocr/winocr.exe'))
        p.wait()
        if os.path.exists("./lib_/loadResult.txt"):
            with open("./lib_/loadResult.txt", "r", encoding="utf-8") as f:
                text = f.read()  # txt to str
            if text == "True":
                return True
        return False

    def getTextTesseractOcr(self, img, folder):
        inputFile = folder + "input.jpg"
        cv2.imwrite(inputFile, img)
        pytesseract.pytesseract.tesseract_cmd = self.tesseractLocation

        if (self.tesseractConfig is not None):
            text = pytesseract.image_to_string(Image.open(inputFile), config=self.tesseractConfig)
        else:
            text = pytesseract.image_to_string(Image.open(inputFile))

        text = self.filterText(text)
        return text

    def getText(self, cropped, folder):
        if self.ocrType == "googleocr":
            text = self.getTextGoogleOcr(cropped)
        elif self.ocrType == "winocr":
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
