from banco.bdUtil import BdUtil, testaConexao
from classes import PrintLog
from processa import ImageProcess
from datetime import datetime
from util import printLog
from defaults import ITENS_PROCESSAR
import os
import sys
sys.path.append("./banco/")


def processar():
    caminhoAplicacao = os.path.abspath('')

    if not os.path.exists(caminhoAplicacao):
        printLog(PrintLog("Caminho para o log não encontrado: " + caminhoAplicacao, caminho=caminhoAplicacao, isSilent=True))
        return

    if not testaConexao():
        printLog(PrintLog("Não foi possivel conectar ao banco de dados.", caminho=caminhoAplicacao, isSilent=True))
        return

    itens = ITENS_PROCESSAR()
    for operacao in itens:
        operacao.caminhoAplicacao = caminhoAplicacao
        try:
            printLog(PrintLog(100*'-', caminho=caminhoAplicacao, isSilent=True))
            if not os.path.exists(operacao.caminho):
                printLog(PrintLog("Caminho não encontrado: " + operacao.caminho, caminho=caminhoAplicacao, isSilent=True))
                continue

            inicio = datetime.now()
            printLog(PrintLog("Iniciando arquivos em: " + operacao.caminho, caminho=caminhoAplicacao, isSilent=True))
            printLog(PrintLog("Inicido do processo: " + inicio.strftime("%H:%M:%S"), caminho=caminhoAplicacao, isSilent=True))
            db = BdUtil(operacao)
            printLog(PrintLog("Criando base " + operacao.base, caminho=caminhoAplicacao, isSilent=True))
            operacao.base = db.criaTabela(operacao.base)
            processa = ImageProcess(operacao)
            printLog(PrintLog("Processando....", caminho=caminhoAplicacao, isSilent=True))
            processa.processaImagens()
            printLog(PrintLog("Concluido", caminho=caminhoAplicacao, isSilent=True))
            printLog(PrintLog("Fim do processo: " + datetime.now().strftime("%H:%M:%S"), caminho=caminhoAplicacao, isSilent=True))
            intervalo = datetime.now() - inicio
            printLog(PrintLog("Tempo decorrido: " + str(intervalo), caminho=caminhoAplicacao, isSilent=True))
        except Exception as e:
            print(e)
            printLog(PrintLog(str(e), caminho=caminhoAplicacao, isSilent=True), arquivo='logError.txt')
            printLog(PrintLog('Error', caminho=caminhoAplicacao, isSilent=True))


if __name__ == '__main__':
    processar()