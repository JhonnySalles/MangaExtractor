from banco.bdUtil import BdUtil, testaConexao
from classes import Operacao, PrintLog
from processa import ImageProcess, extraiNomeDiretorio
from datetime import datetime
import os
import threading
import PySimpleGUI as sg
import sys
from util import printLog

from PySimpleGUI.PySimpleGUI import ConvertArgsToSingleString
sys.path.append("./banco/")

# Simular um teste sem abrir a janela
isTeste = False

###################################################
def teste():
    operacao = Operacao("teste",  "teste", "F:/Manga2", "ja")
    operacao.ocrType = 'tesseract'
    operacao.isTeste = isTeste
    operacao.furigana = True
    operacao.textoVertical = True

    db = BdUtil(operacao)
    operacao.base = db.criaTabela(operacao.base)

    processa = ImageProcess(operacao)
    processa.processaImagens()


#################################################
sg.theme('Black')   # Cores
# Layout
layout = [[sg.Text('Caminho', text_color='orangered', size=(15, 1)), sg.Input(key='-CAMINHO-', enable_events=True, default_text='C:/'), sg.FolderBrowse('Selecionar pasta')],
          [sg.Text('Nome Manga', text_color='cornflowerblue', size=(15, 1)), sg.Input(key='-MANGA-', enable_events=True)],
          [sg.Text('Volume', size=(15, 1)), sg.InputText(key='-VOLUME-')],
          [sg.Text('Capitulo', size=(15, 1)), sg.InputText(key='-CAPITULO-')],
          [sg.Text('Scan', size=(15, 1)), sg.InputText(key='-SCAN-')],
          [sg.Text('Base', text_color='orangered', size=(15, 1)), sg.InputText(key='-BASE-')],
          [sg.Text('Caminho Tesseract', text_color='cornflowerblue', size=(15, 1)), sg.Input(key='-TESSERACT_LOCATE-', default_text='C:/Program Files/Tesseract-OCR'), sg.FolderBrowse('Selecionar pasta')],
          [sg.Text('Linguagem', size=(15, 1)), sg.Combo(['Português', 'Japonês', 'Inglês', 'Japonês (vertical)', 'Japonês (horizontal)'], default_value='Japonês', key='-LINGUAGEM-', size=(15, 1), enable_events=True)],
          [sg.Text('Recurso OCR', size=(15, 1)), sg.Combo(['WinOCR', 'Tesseract'], default_value='Tesseract', key='-OCRTYPE-', size=(15, 1))],
          [sg.Checkbox('Carregar Informações da pasta?', default=True, key="-GET_INFORMACAO-", size=(30, 1)), sg.Checkbox('Limpar furigana?', default=False, key="-FURIGANA-")],
          [sg.Checkbox('Obter o nome do manga da pasta?', default=False, key="-GET_NOME-", size=(30, 1)), sg.Checkbox('Filtro adicional para limpar o furigana?', default=False, key="-FILTRO_ADICIONAL_FURIGANA-")],
          [sg.Multiline(size=(80, 10), key='-OUTPUT-')],
          [sg.ProgressBar(100, orientation='h', size=(44, 5), key='-PROGRESSBAR-')],
          [sg.Button('Ok', size=(30, 1)), sg.Text('', size=(7, 1)), sg.Button('Cancel', size=(30, 1))]]

# Create the Window
window = sg.Window('Manga Text Extractor', layout)
progress = window['-PROGRESSBAR-']
LOGMEMO = window['-OUTPUT-']
operacao = None


def validaCampos(values):
    if values['-OCRTYPE-'].lower() == 'tesseract':
        file = ''.join(values['-TESSERACT_LOCATE-'].strip()).replace('\\', '/').replace('//', '/').replace('tesseract.exe', '')
        if (values['-TESSERACT_LOCATE-'].strip() == '') or (not os.path.isfile(file + '/tesseract.exe')):
            aviso('Tesseract não encontrado, favor verificar o caminho informado!')
            return False

    if (values['-CAMINHO-'].strip() == ''):
        aviso('Favor informar um caminho de origem!')
        return False
    elif not os.path.exists(''.join(values['-CAMINHO-']).replace('\\', '/').replace('//', '/')):
        aviso('Caminho informado não encontrado!')
        return False

    if (values['-MANGA-'].strip() == '') and ((not values['-GET_NOME-']) or (values['-GET_INFORMACAO-'])):
        aviso('Favor informar um nome!')
        return False

    if (values['-BASE-'].strip() == ''):
        aviso('Favor informar uma base!')
        return False

    return True


def aviso(text):
    sg.Popup(text, title='Aviso')


def carrega(values):
    vertical = None
    linguagem = ""
    if (values['-LINGUAGEM-'] == 'Japonês'):
        linguagem = "ja"
    elif (values['-LINGUAGEM-'] == 'Inglês'):
        linguagem = "en"
    elif (values['-LINGUAGEM-'] == 'Japonês (horizontal)'):
        linguagem = "ja"
        vertical = False
    elif (values['-LINGUAGEM-'] == 'Japonês (vertical)'):
        linguagem = "ja"
        vertical = True
    else:
        linguagem = "pt"

    global operacao # Usa a variavel global
    operacao = Operacao(values['-BASE-'], values['-MANGA-'], values['-CAMINHO-'], linguagem, window)

    operacao.volume = values['-VOLUME-']
    operacao.capitulo = values['-CAPITULO-']
    operacao.scan = values['-SCAN-']
    operacao.getNomePasta = values['-GET_NOME-']
    operacao.getInformacaoPasta = values['-GET_INFORMACAO-']
    operacao.ocrType = values['-OCRTYPE-'].lower()
    operacao.pastaTesseract = ''.join(values['-TESSERACT_LOCATE-'].strip()).replace('\\', '/').replace('//', '/').replace('tesseract.exe', '')
    operacao.textoVertical = vertical
    operacao.furigana = False if linguagem != "ja" else values['-FURIGANA-']
    operacao.filtroAdicional = False if linguagem != "ja" else values['-FILTRO_ADICIONAL_FURIGANA-']
    return operacao


def processar(operacao):
    db = BdUtil(operacao)
    operacao.base = db.criaTabela(operacao.base)

    processa = ImageProcess(operacao)
    processa.processaImagens()


def thread_process(operacao, window):
    processar(operacao)
    window.write_event_value('-THREAD_END-', 'Processamento concluído com sucesso. \nManga: ' + operacao.mangaNome) 


def eventoManga(values):
    window['-BASE-'].Update(values['-MANGA-'])


def extraiInformacoesDiretorio(values):
    caminho = values["-CAMINHO-"]

    if (os.path.exists(caminho)):
        manga = values["-MANGA-"]
        pasta = ""

        for diretorio, subpastas, arquivos in os.walk(caminho):
            if "tmp" in subpastas:  # Ignora as pastas temporárias da busca
                subpastas.remove("tmp")

            if len(subpastas) < 1:
                return

            pasta = subpastas[0]
            manga = extraiNomeDiretorio(pasta)
            break

        window['-MANGA-'].Update(manga)
        window['-BASE-'].Update(manga)


def main():
    if isTeste:
        teste()
    else:
        global operacao
        MaxProgress = 1
        inicio = datetime.now()
        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
                break
            elif event == '-CAMINHO-':
                extraiInformacoesDiretorio(values)
            elif event == '-MANGA-':
                eventoManga(values)
            elif event == '-LINGUAGEM-':
                if "japonês" not in values['-LINGUAGEM-'].lower():
                   window['-FURIGANA-'].update(value=False, disabled=True)
                   window['-FILTRO_ADICIONAL_FURIGANA-'].update(value=False, disabled=True)
                else:
                    window['-FURIGANA-'].update(disabled=False)  
                    window['-FILTRO_ADICIONAL_FURIGANA-'].update(disabled=False)  
            elif event == 'Ok':
                if not testaConexao():
                    aviso('Não foi possível conectar ao banco de dados')
                elif validaCampos(values):
                    inicio = datetime.now()
                    LOGMEMO.Update('')
                    operacao = carrega(values)
                    printLog(PrintLog('Inicido do processo: ' + inicio.strftime("%H:%M:%S"), 'yellow', logMemo=LOGMEMO, caminho=operacao.caminho))
                    threading.Thread(target=thread_process,args=(operacao, window),daemon=True).start()
            elif event == '-THREAD_AVISO-':
                aviso(values[event])
            elif event == '-THREAD_LOG-':
                prtLog = values[event]
                prtLog.logMemo = LOGMEMO
                prtLog.caminho = operacao.caminho 
                printLog(prtLog)
            elif event == '-THREAD_PROGRESSBAR_UPDATE-':
                progress.UpdateBar(values[event], MaxProgress)
            elif event == '-THREAD_PROGRESSBAR_MAX-':
                MaxProgress = values[event]
            elif event == '-THREAD_END-':
                intervalo = datetime.now() - inicio
                progress.UpdateBar(MaxProgress, MaxProgress)
                printLog(PrintLog('Fim do processo: ' + datetime.now().strftime("%H:%M:%S"), 'yellow', logMemo=LOGMEMO, caminho=operacao.caminho))
                printLog(PrintLog('Tempo decorrido: ' + str(intervalo), 'yellow', logMemo=LOGMEMO, caminho=operacao.caminho))
                if operacao.furigana:
                    printLog(PrintLog('Com limpeza de furigana.', logMemo=LOGMEMO, caminho=operacao.caminho))
                aviso(values[event])

        window.close()


if __name__ == '__main__':
    main()
