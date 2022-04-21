from banco.bdUtil import BdUtil, testConnection
from classes import PrintLog
from process import ImageProcess
from datetime import datetime
from util import printLog
from defaults import PROCESS_ITEMS
import os
import sys
sys.path.append("./banco/")


def process():
    applicationPath = os.path.abspath('')

    if not os.path.exists(applicationPath):
        printLog(PrintLog("Caminho para o log não encontrado: " + applicationPath, directory=applicationPath, isSilent=True))
        return

    if not testConnection():
        printLog(PrintLog("Não foi possivel conectar ao banco de dados.", directory=applicationPath, isSilent=True))
        return

    for operation in PROCESS_ITEMS():
        operation.applicationPath = applicationPath
        try:
            printLog(PrintLog(100*'-', directory=applicationPath, isSilent=True))
            if not os.path.exists(operation.directory):
                printLog(PrintLog("Caminho não encontrado: " + operation.directory, directory=applicationPath, isSilent=True))
                continue

            initialTime = datetime.now()
            printLog(PrintLog("Iniciando files em: " + operation.directory, directory=applicationPath, isSilent=True))
            printLog(PrintLog("Inicido do processo: " + initialTime.strftime("%H:%M:%S"), directory=applicationPath, isSilent=True))
            db = BdUtil(operation)
            printLog(PrintLog("Criando base " + operation.base, directory=applicationPath, isSilent=True))
            operation.base = db.createTable(operation.base)
            process = ImageProcess(operation)
            printLog(PrintLog("Processando....", directory=applicationPath, isSilent=True))
            process.processImages()
            printLog(PrintLog("Concluido", directory=applicationPath, isSilent=True))
            printLog(PrintLog("Fim do processo: " + datetime.now().strftime("%H:%M:%S"), directory=applicationPath, isSilent=True))
            interval = datetime.now() - initialTime
            printLog(PrintLog("Tempo decorrido: " + str(interval), directory=applicationPath, isSilent=True))
        except Exception as e:
            print(e)
            printLog(PrintLog(str(e), directory=applicationPath, isSilent=True), file='logError.txt')
            printLog(PrintLog('Error', directory=applicationPath, isSilent=True))


if __name__ == '__main__':
    process()