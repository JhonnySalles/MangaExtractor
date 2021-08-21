from banco.bdUtil import BdUtil, testaConexao
from classes import Operacao
from processa import ImageProcess
from datetime import datetime
import os
import sys
sys.path.append("./banco/")


def itensProcessar():
    operacoes = []
    operacoes.append(Operacao("teste",  "teste", "F:/Manga2", "ja", furigana=True))

    return operacoes


def printLog(text, arquivo='log.txt'):
    #print(text)
    with open(arquivo, 'a+', encoding='utf-8') as file:
        file.write(text + '\n')


def processar():
    if not testaConexao():
        printLog("Não foi possivel conectar ao banco de dados.")
        return

    itens = itensProcessar()
    for operacao in itens:
        try:
            printLog(100*'-')
            if not os.path.exists(operacao.caminho):
                printLog("Caminho não encontrado: " + operacao.caminho)
                continue

            inicio = datetime.now()
            printLog("Iniciando arquivo " + operacao.caminho)
            printLog("Inicido do processo: " + inicio.strftime("%H:%M:%S"))
            db = BdUtil(operacao)
            printLog("Criando base " + operacao.base)
            operacao.base = db.criaTabela(operacao.base)
            processa = ImageProcess(operacao)
            printLog("Processando....")
            processa.processaImagens()
            printLog("Concluido")
            printLog("Fim do processo: " + datetime.now().strftime("%H:%M:%S"))
            intervalo = datetime.now() - inicio
            printLog("Tempo decorrido: " + str(intervalo))
        except Exception as e:
            printLog(str(e), arquivo='logError.txt')
            print(e)
            printLog('Error')


if __name__ == '__main__':
    processar()