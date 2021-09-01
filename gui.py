from banco.bdUtil import BdUtil, testaConexao
from classes import Operacao, PrintLog
from processa import ImageProcess, extraiNomeDiretorio, extraiInformacoesDiretorio
from datetime import datetime
import os
import threading
import PySimpleGUI as sg
import sys
from util import printLog
from unidecode import unidecode
from termcolor import colored
import globals

from PySimpleGUI.PySimpleGUI import ConvertArgsToSingleString
sys.path.append("./banco/")


# Simular um teste sem abrir a janela
isTeste = False

###################################################
def teste():
    OPERACAO = Operacao("kami nomi",  "The World God Only Knows", "F:/Manga/Portuguese3", "pt")
    OPERACAO.ocrType = 'tesseract'
    OPERACAO.isTeste = isTeste
    OPERACAO.furigana = False
    OPERACAO.textoVertical = False

    db = BdUtil(OPERACAO)
    OPERACAO.base = db.criaTabela(OPERACAO.base)

    processa = ImageProcess(OPERACAO)
    processa.processaImagens()


#################################################
sg.theme('Black')   # Cores
headings = ['Operação', 'Base', 'Manga', 'Caminho', 'Furigana?', 'Idioma', '']
listaOperacoes = []
# Layout

tabOperacao = [[sg.Multiline(size=(80, 11), key='-OUTPUT-')],
               [sg.Button('Processar', key='-BTN_PROCESSAR-', size=(30, 1), use_ttk_buttons=True, disabled_button_color=('white', 'black')), sg.Text('', size=(7, 1)), sg.Button('Cancelar', key='-BTN_CANCELAR-', size=(30, 1), use_ttk_buttons=True, disabled_button_color=('white', 'black'))]]

tabLista = [[sg.Table(listaOperacoes, headings=headings, justification='left', key='-TABLE-', display_row_numbers=False, enable_events=True, auto_size_columns=False, col_widths=[0, 10, 19, 20, 7, 5, 2], size=(80, 10))],
            [sg.Button('Inserir', size=(20, 1), key='-BTN_INSERIR-', use_ttk_buttons=True, disabled_button_color=('white', 'black')), sg.Text('', size=(2, 1)), sg.Button('Remover', key='-BTN_REMOVER-', size=(20, 1), use_ttk_buttons=True, disabled_button_color=('white', 'black')), sg.Text('', size=(2, 1)), sg.Button('Processar Lista', key='-BTN_PROCESSAR_LISTA-', size=(20, 1), use_ttk_buttons=True, disabled_button_color=('white', 'black'))]]

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
          [sg.TabGroup([[sg.Tab('Operação', tabOperacao), sg.Tab('Lista operações', tabLista)]])],
          [sg.ProgressBar(100, orientation='h', size=(45, 5), key='-PROGRESSBAR-')]]

# Create the Window
window = sg.Window('Manga Text Extractor', layout)
PROGRESS = window['-PROGRESSBAR-']
LOGMEMO = window['-OUTPUT-']
OPERACAO = None
SELECTED_ROW = None

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


def enableButtons():
    window['-BTN_PROCESSAR-'].Update(disabled=False)
    window['-BTN_CANCELAR-'].Update(disabled=False)
    window['-BTN_PROCESSAR_LISTA-'].Update(disabled=False)
    window['-BTN_INSERIR-'].Update(disabled=False)
    window['-BTN_REMOVER-'].Update(disabled=False)
    window['-BTN_PROCESSAR-'].Update(text='Processar')
    window['-BTN_PROCESSAR_LISTA-'].Update(text='Processar Lista')


def disableButtons(operacao):
    window['-BTN_CANCELAR-'].Update(disabled=True)
    window['-BTN_INSERIR-'].Update(disabled=True)
    window['-BTN_REMOVER-'].Update(disabled=True)

    if operacao.upper() == 'OPERAÇÃO':
        window['-BTN_PROCESSAR-'].Update(text='Parar processamento')
        window['-BTN_PROCESSAR_LISTA-'].Update(disabled=True)
    elif operacao.upper() == 'LISTA':
        window['-BTN_PROCESSAR-'].Update(disabled=True)
        window['-BTN_PROCESSAR_LISTA-'].Update(text='Parar processamento')


def limpaCampos():
    window['-CAMINHO-'].Update('C:/')
    window['-MANGA-'].Update('')
    window['-VOLUME-'].Update('')
    window['-CAPITULO-'].Update('')
    window['-SCAN-'].Update('')
    window['-BASE-'].Update('')
    window['-GET_INFORMACAO-'].Update(True)
    window['-GET_NOME-'].Update(False)
    window['-FURIGANA-'].Update(False)
    window['-FILTRO_ADICIONAL_FURIGANA-'].Update(False)
    window['-FILTRO_ADICIONAL_FURIGANA-'].Update(False)


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

    global OPERACAO # Usa a variavel global
    OPERACAO = Operacao(values['-BASE-'], values['-MANGA-'], values['-CAMINHO-'], linguagem, window)

    OPERACAO.volume = values['-VOLUME-']
    OPERACAO.capitulo = values['-CAPITULO-']
    OPERACAO.scan = values['-SCAN-']
    OPERACAO.getNomePasta = values['-GET_NOME-']
    OPERACAO.getInformacaoPasta = values['-GET_INFORMACAO-']
    OPERACAO.ocrType = values['-OCRTYPE-'].lower()
    OPERACAO.pastaTesseract = ''.join(values['-TESSERACT_LOCATE-'].strip()).replace('\\', '/').replace('//', '/').replace('tesseract.exe', '')
    OPERACAO.textoVertical = vertical
    OPERACAO.furigana = False if linguagem != "ja" else values['-FURIGANA-']
    OPERACAO.filtroAdicional = False if linguagem != "ja" else values['-FILTRO_ADICIONAL_FURIGANA-']
    return OPERACAO


def processar(operacao):
    db = BdUtil(operacao)
    operacao.base = db.criaTabela(operacao.base)

    processa = ImageProcess(operacao)
    processa.processaImagens()


def thread_process(operacao, window):
    globals.CANCELAR_OPERACAO = False
    try:
        processar(operacao)
        window.write_event_value('-THREAD_END-', 'Processamento concluído com sucesso. \nManga: ' + operacao.mangaNome)
    except Exception as e:
        window.write_event_value('-THREAD_ERROR-', str(e))


def thread_list_process(listaOperacao, window):
    globals.CANCELAR_OPERACAO = False
    mangas = ''

    if not isTeste:
        window.write_event_value('-THREAD_LOG-', PrintLog("Iniciando a lista de operações com " + str(len(listaOperacao)) + " operações...", 'magenta'))
    else:
        print(colored("Iniciando a lista de operações com " + str(len(listaOperacao)) + " operações...", 'magenta', attrs=['reverse', 'blink']))

    try:
        for item in listaOperacao:
            global OPERACAO # Usa a variavel global
            OPERACAO = item[0]
            inicioManga = datetime.now()
            if not isTeste:
                window.write_event_value('-THREAD_LOG-', PrintLog("Inicio do processo do manga " + OPERACAO.mangaNome + " da lista de operações.", 'magenta'))
                window.write_event_value('-THREAD_LOG-', PrintLog('Inicio do processo: ' + inicioManga.strftime("%H:%M:%S"), 'magenta'))
            else:
                print(colored("Inicio do processo do manga " + OPERACAO.mangaNome + " da lista de operações.", 'magenta', attrs=['reverse', 'blink']))
                print(colored('Inicio do processo: ' + inicioManga.strftime("%H:%M:%S"), 'yellow', attrs=['reverse', 'blink']))

            processar(OPERACAO)

            if not globals.CANCELAR_OPERACAO:
                mangas += OPERACAO.mangaNome + ', '
                item[-1] = 'X'
                intervaloManga = datetime.now() - inicioManga
                if not isTeste:
                    window.write_event_value('-THREAD_LOG-', PrintLog("Manga processado com exito.... " + OPERACAO.mangaNome, 'magenta'))
                    window.write_event_value('-THREAD_LOG-', PrintLog('Fim do processo: ' + datetime.now().strftime("%H:%M:%S"), 'yellow'))
                    window.write_event_value('-THREAD_LOG-', PrintLog('Tempo decorrido: ' + str(intervaloManga), 'yellow'))
                    window.write_event_value('-THREAD_LOG-', PrintLog(100*'-'))
                    window.write_event_value('-THREAD_LIST_UPDATE-', listaOperacao)
                else:
                    print(colored("Manga processado com exito.... " + OPERACAO.mangaNome, 'magenta', attrs=['reverse', 'blink']))
                    print(colored('Fim do processo: ' + datetime.now().strftime("%H:%M:%S"), 'yellow', attrs=['reverse', 'blink']))
                    print(colored('Tempo decorrido: ' + str(intervaloManga), 'yellow', attrs=['reverse', 'blink']))
                    print(100*'-')
        
        if not globals.CANCELAR_OPERACAO:    
            mangas = mangas[:mangas.rindex(", ")]

        window.write_event_value('-THREAD_END-', 'Processamento da lista concluído com sucesso. \nMangas processados: ' + mangas) 
    except Exception as e:
        window.write_event_value('-THREAD_ERROR-', str(e)) 



def eventoManga(values):
    window['-BASE-'].Update(unidecode(values['-MANGA-'].strip()))


def eventoCaminho(values):
    caminho = values["-CAMINHO-"]

    if (os.path.exists(caminho)):
        manga = values["-MANGA-"]
        pasta = ""

        for diretorio, subpastas, arquivos in os.walk(caminho):
            subpastas[:] = [sub for sub in subpastas if sub not in ['tmp']]
            subpastas[:] = [sub for sub in subpastas if "capa" not in sub.lower()]

            if len(subpastas) < 1:
                return
                
            pasta = subpastas[0]
            manga = extraiNomeDiretorio(pasta)
            capitulo = extraiInformacoesDiretorio(pasta, manga)
            break

        window['-MANGA-'].Update(manga)
        window['-VOLUME-'].Update(capitulo.volume)
        window['-CAPITULO-'].Update(capitulo.capitulo)
        window['-SCAN-'].Update(capitulo.scan)
        window['-BASE-'].Update(unidecode(manga.replace("-", " "))[:40].strip())


def main():
    if isTeste:
        teste()
    else:
        global OPERACAO
        MaxProgress = 1
        inicio = datetime.now()
        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED or event == '-BTN_CANCELAR-':
                break
            elif event == '-CAMINHO-':
                eventoCaminho(values)
            elif event == '-MANGA-':
                eventoManga(values)
            elif event == '-TABLE-':
                SELECTED_ROW = values['-TABLE-'][0]
            elif event == '-LINGUAGEM-':
                if "japonês" not in values['-LINGUAGEM-'].lower():
                   window['-FURIGANA-'].update(value=False, disabled=True)
                   window['-FILTRO_ADICIONAL_FURIGANA-'].update(value=False, disabled=True)
                else:
                    window['-FURIGANA-'].update(disabled=False)  
                    window['-FILTRO_ADICIONAL_FURIGANA-'].update(disabled=False)  
            elif event == '-BTN_INSERIR-':
                if validaCampos(values):
                    itemFila = carrega(values)
                    listaOperacoes.append([itemFila, itemFila.base, itemFila.mangaNome, itemFila.caminho, itemFila.furigana, itemFila.linguagem, ' - '])
                    window['-TABLE-'].update(values=listaOperacoes)
                    limpaCampos()
            elif event == '-BTN_REMOVER-':
                if len(listaOperacoes) > 0:
                    if (SELECTED_ROW is not None):
                        listaOperacoes.pop(SELECTED_ROW)
                    else:
                        listaOperacoes.pop()
                    window['-TABLE-'].update(values=listaOperacoes)
                SELECTED_ROW = None
            elif ((event == '-BTN_PROCESSAR-') or (event == '-BTN_PROCESSAR_LISTA-')) and (window[event].get_text() == 'Parar processamento'):
                globals.CANCELAR_OPERACAO = True
            elif (event == '-BTN_PROCESSAR-') or  (event == '-BTN_PROCESSAR_LISTA-'):
                if not testaConexao():
                    aviso('Não foi possível conectar ao banco de dados')
                if (event == '-BTN_PROCESSAR_LISTA-'):
                    if len(listaOperacoes) == 0:
                        aviso('Nenhuma operação na lista.')
                    else:
                        disableButtons("LISTA")
                        inicio = datetime.now()
                        LOGMEMO.Update('')
                        printLog(PrintLog('Inicio do processo: ' + inicio.strftime("%H:%M:%S"), 'yellow', logMemo=LOGMEMO, caminho=os.path.abspath('')))
                        threading.Thread(target=thread_list_process,args=(listaOperacoes, window),daemon=True).start()
                elif validaCampos(values):
                    disableButtons("OPERAÇÃO")
                    inicio = datetime.now()
                    LOGMEMO.Update('')
                    OPERACAO = carrega(values)
                    printLog(PrintLog('Inicio do processo: ' + inicio.strftime("%H:%M:%S"), 'yellow', logMemo=LOGMEMO, caminho=OPERACAO.caminho))
                    threading.Thread(target=thread_process,args=(OPERACAO, window),daemon=True).start()
            elif event == '-THREAD_AVISO-':
                aviso(values[event])
            elif event == '-THREAD_LOG-':
                prtLog = values[event]
                prtLog.logMemo = LOGMEMO
                prtLog.caminho = OPERACAO.caminho 
                printLog(prtLog)
            elif event == '-THREAD_PROGRESSBAR_UPDATE-':
                PROGRESS.UpdateBar(values[event], MaxProgress)
            elif event == '-THREAD_PROGRESSBAR_MAX-':
                MaxProgress = values[event]
            elif event == '-THREAD_LIST_UPDATE-':
                window['-TABLE-'].update(values=values[event])
            elif event == '-THREAD_ERROR-':
                aviso('Erro no processamento.... ', values[event])
                enableButtons()
            elif event == '-THREAD_END-':
                if globals.CANCELAR_OPERACAO:
                    printLog(PrintLog('Operação cancelada...', 'yellow', logMemo=LOGMEMO, caminho=OPERACAO.caminho))
                    aviso('Processamento parado.')
                else:
                    PROGRESS.UpdateBar(MaxProgress, MaxProgress)
                    intervalo = datetime.now() - inicio
                    printLog(PrintLog('Fim do processo: ' + datetime.now().strftime("%H:%M:%S"), 'yellow', logMemo=LOGMEMO, caminho=OPERACAO.caminho))
                    printLog(PrintLog('Tempo decorrido: ' + str(intervalo), 'yellow', logMemo=LOGMEMO, caminho=OPERACAO.caminho))
                    if OPERACAO.furigana:
                        printLog(PrintLog('Com limpeza de furigana.', logMemo=LOGMEMO, caminho=OPERACAO.caminho))
                    aviso(values[event])
                enableButtons()

        window.close()


if __name__ == '__main__':
    main()
