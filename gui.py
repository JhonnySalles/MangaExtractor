from banco.bdUtil import BdUtil, testConnection
from classes import Operation, PrintLog, Config
from process import ImageProcess, getDirectoryName, getDirectoryInformation, moveFilesDirectories
from datetime import datetime
import os
import threading
import PySimpleGUI as sg
import sys
from util import printLog, saveConfig, readConfig
from unidecode import unidecode
from termcolor import colored
import globals
from banco.bdUtil import findTable

from PySimpleGUI.PySimpleGUI import ConvertArgsToSingleString
sys.path.append("./banco/")


# Simular um teste sem abrir a janela
ISTEST = False

###################################################
def teste():
    OPERATION = Operation("kami nomi",  "The World God Only Knows", r"F:/Manga/Teste", "pt")
    OPERATION.ocrType = 'tesseract'
    OPERATION.isTest = ISTEST
    OPERATION.furigana = False
    OPERATION.verticalText = False

    db = BdUtil(OPERATION)
    OPERATION.base = db.createTable(OPERATION.base)

    process = ImageProcess(OPERATION)
    process.processImages()


#################################################
sg.theme('Black')   # Cores
headings = ['Operação', 'Base', 'Manga', 'Caminho', 'Furigana', 'Idioma', '']
listOperations = []
# Layout

tabOperation = [[sg.Multiline(size=(80, 11), key='-OUTPUT-')],
               [sg.Button('Processar', key='-BTN_PROCESS-', size=(30, 1), use_ttk_buttons=True, disabled_button_color=('white', 'black')), sg.Text('', size=(7, 1)), sg.Button('Cancelar', key='-BTN_CANCEL-', size=(30, 1), use_ttk_buttons=True, disabled_button_color=('white', 'black'))]]

tabLista = [[sg.Table(listOperations, headings=headings, justification='left', key='-TABLE-', display_row_numbers=False, enable_events=True, auto_size_columns=False, col_widths=[0, 10, 19, 20, 7, 5, 2], size=(80, 10))],
            [sg.Button('Inserir', size=(20, 1), key='-BTN_INSERT-', use_ttk_buttons=True, disabled_button_color=('white', 'black')), sg.Text('', size=(2, 1)), sg.Button('Remover', key='-BTN_REMOVE-', size=(20, 1), use_ttk_buttons=True, disabled_button_color=('white', 'black')), sg.Text('', size=(2, 1)), sg.Button('Processar Lista', key='-BTN_PROCESS_LIST-', size=(20, 1), use_ttk_buttons=True, disabled_button_color=('white', 'black'))]]

tabMoverImagens = [[sg.Text('Nome da pasta', size=(15, 1)), sg.Input(key='-FOLDER_NAME-', default_text='Manga')],
                   [sg.Text('Caminho Origem', size=(15, 1)), sg.Input(key='-FROM_PATH-', default_text='C:/'), sg.FolderBrowse('Selecionar pasta')],
                   [sg.Text('Caminho Destino', size=(15, 1)), sg.Input(key='-TO_PATH-', default_text='C:/'), sg.FolderBrowse('Selecionar pasta')],
                   [sg.Button('Copiar os arquivos', size=(20, 1), key='-BTN_COPY_FILES-', use_ttk_buttons=True, disabled_button_color=('white', 'black'))]]

layout = [[sg.Text('Caminho', text_color='orangered', size=(15, 1)), sg.Input(key='-DIRECTORY-', enable_events=True, default_text='C:/'), sg.FolderBrowse('Selecionar pasta')],
          [sg.Text('Nome Manga', text_color='cornflowerblue', size=(15, 1)), sg.Input(key='-MANGA-', enable_events=True)],
          [sg.Text('Volume', size=(15, 1)), sg.InputText(key='-VOLUME-')],
          [sg.Text('Chapter', size=(15, 1)), sg.InputText(key='-CHAPTER-')],
          [sg.Text('Scan', size=(15, 1)), sg.InputText(key='-SCAN-')],
          [sg.Text('Base', key='-LABELBASE-', text_color='white', size=(15, 1)), sg.InputText(key='-BASE-')],
          [sg.Text('Caminho Tesseract', text_color='cornflowerblue', size=(15, 1)), sg.Input(key='-TESSERACT_LOCATE-', default_text='C:/Program Files/Tesseract-OCR'), sg.FolderBrowse('Selecionar pasta')],
          [sg.Text('Linguagem', size=(15, 1)), sg.Combo(['Português', 'Japonês', 'Inglês', 'Japonês (vertical)', 'Japonês (horizontal)'], default_value='Japonês', key='-LANGUAGE-', size=(15, 1), enable_events=True), sg.Text('', key='-LASTVOLUME-', text_color='white')],
          [sg.Text('Recurso OCR', size=(15, 1)), sg.Combo(['WinOCR', 'Tesseract'], default_value='Tesseract', key='-OCRTYPE-', size=(15, 1))],
          [sg.Checkbox('Carregar Informações da pasta?', default=True, key="-GET_INFORMATION-", size=(30, 1)), sg.Checkbox('Limpar furigana?', default=False, key="-FURIGANA-")],
          [sg.Checkbox('Obter o nome do manga da pasta?', default=True, key="-GET_NAME-", size=(30, 1)), sg.Checkbox('Filtro adicional para limpar o furigana?', default=False, key="-ADDITIONAL_FILTER_FURIGANA-")],
          [sg.TabGroup([[sg.Tab('Operação', tabOperation), sg.Tab('Lista operações', tabLista), sg.Tab('Montar estrutura de arquivos', tabMoverImagens)]])],
          [sg.ProgressBar(100, orientation='h', size=(45, 5), key='-PROGRESSBAR-')]]

# Create the Window
window = sg.Window('Manga Text Extractor', layout)
PROGRESS = window['-PROGRESSBAR-']
LOGMEMO = window['-OUTPUT-']
OPERATION = None
SELECTED_ROW = []
LAST_DIRECTORY = None

def validateFields(values):
    if values['-OCRTYPE-'].lower() == 'tesseract':
        file = ''.join(values['-TESSERACT_LOCATE-'].strip()).replace('\\', '/').replace('//', '/').replace('tesseract.exe', '')
        if (values['-TESSERACT_LOCATE-'].strip() == '') or (not os.path.isfile(file + '/tesseract.exe')):
            alert('Tesseract não encontrado, favor verificar o diretório informado!')
            return False

    if (values['-DIRECTORY-'].strip() == ''):
        alert('Favor informar um diretório de origem!')
        return False
    elif not os.path.exists(''.join(values['-DIRECTORY-']).replace('\\', '/').replace('//', '/')):
        alert('Caminho informado não encontrado!')
        return False

    if (values['-MANGA-'].strip() == '') and ((not values['-GET_NAME-']) or (values['-GET_INFORMATION-'])):
        alert('Favor informar um nome!')
        return False

    if (values['-BASE-'].strip() == ''):
        window['-LABELBASE-'].Update('text_color=orangered')
        alert('Favor informar uma base!')
        return False

    saveConfig(Config(values['-DIRECTORY-'], values['-MANGA-'], values['-VOLUME-'], values['-CHAPTER-'], values['-SCAN-'], values['-BASE-'], values['-LANGUAGE-'],  
            values['-OCRTYPE-'], values['-GET_INFORMATION-'], values['-GET_NAME-'], values['-FURIGANA-'], values['-ADDITIONAL_FILTER_FURIGANA-']))
    return True


def enableButtons():
    window['-BTN_PROCESS-'].Update(disabled=False)
    window['-BTN_CANCEL-'].Update(disabled=False)
    window['-BTN_PROCESS_LIST-'].Update(disabled=False)
    window['-BTN_INSERT-'].Update(disabled=False)
    window['-BTN_REMOVE-'].Update(disabled=False)
    window['-BTN_PROCESS-'].Update(text='Processar')
    window['-BTN_PROCESS_LIST-'].Update(text='Processar Lista')
    window['-BTN_COPY_FILES-'].Update(text='Copiar os arquivos')


def disableButtons(operation):
    window['-BTN_CANCEL-'].Update(disabled=True)
    window['-BTN_INSERT-'].Update(disabled=True)
    window['-BTN_REMOVE-'].Update(disabled=True)

    if operation.upper() == 'COPIA ARQUIVOS':
        window['-BTN_COPY_FILES-'].Update(text='Parar processamento')
        window['-BTN_PROCESS-'].Update(disabled=True)
        window['-BTN_PROCESS_LIST-'].Update(disabled=True)
    elif operation.upper() == 'OPERAÇÃO':
        window['-BTN_PROCESS-'].Update(text='Parar processamento')
        window['-BTN_PROCESS_LIST-'].Update(disabled=True)
    elif operation.upper() == 'LISTA':
        window['-BTN_PROCESS-'].Update(disabled=True)
        window['-BTN_PROCESS_LIST-'].Update(text='Parar processamento')


def cleanFields():
    global LAST_DIRECTORY
    LAST_DIRECTORY = None
    window['-LABELBASE-'].Update('Base', text_color='white')
    window['-DIRECTORY-'].Update('C:/')
    window['-MANGA-'].Update('')
    window['-VOLUME-'].Update('')
    window['-CHAPTER-'].Update('')
    window['-SCAN-'].Update('')
    window['-BASE-'].Update('')
    window['-GET_INFORMATION-'].Update(True)
    window['-GET_NAME-'].Update(True)
    window['-FURIGANA-'].Update(False)
    window['-ADDITIONAL_FILTER_FURIGANA-'].Update(False)


def alert(text):
    sg.Popup(text, title='Aviso')


def acronymLanguage(language):
    acronym = ""
    if (language == 'Japonês'):
        acronym = "ja"
    elif (language == 'Inglês'):
        acronym = "en"
    elif (language == 'Japonês (horizontal)'):
        acronym = "ja"
    elif (language == 'Japonês (vertical)'):
        acronym = "ja"

    return acronym


def load(values):
    vertical = None
    language = ""
    if (values['-LANGUAGE-'] == 'Japonês'):
        language = "ja"
    elif (values['-LANGUAGE-'] == 'Inglês'):
        language = "en"
    elif (values['-LANGUAGE-'] == 'Japonês (horizontal)'):
        language = "ja"
        vertical = False
    elif (values['-LANGUAGE-'] == 'Japonês (vertical)'):
        language = "ja"
        vertical = True
    else:
        language = "pt"

    global OPERATION # Usa a variavel global
    OPERATION = Operation(values['-BASE-'], values['-MANGA-'], values['-DIRECTORY-'], language, window)

    OPERATION.volume = values['-VOLUME-']
    OPERATION.chapter = values['-CHAPTER-']
    OPERATION.scan = values['-SCAN-']
    OPERATION.getNameFolder = values['-GET_NAME-']
    OPERATION.getFolderInformation = values['-GET_INFORMATION-']
    OPERATION.ocrType = values['-OCRTYPE-'].lower()
    OPERATION.tesseractFolder = ''.join(values['-TESSERACT_LOCATE-'].strip()).replace('\\', '/').replace('//', '/').replace('tesseract.exe', '')
    OPERATION.verticalText = vertical
    OPERATION.furigana = False if language != "ja" else values['-FURIGANA-']
    OPERATION.furiganaFilter = False if language != "ja" else values['-ADDITIONAL_FILTER_FURIGANA-']
    return OPERATION


def process(operation):
    db = BdUtil(operation)
    operation.base = db.createTable(operation.base)

    process = ImageProcess(operation)
    process.processImages()


def thread_process(operation, window):
    globals.CANCEL_OPERATION = False
    try:
        process(operation)
        window.write_event_value('-THREAD_END-', 'Processamento concluído com sucesso. \nManga: ' + operation.nameManga)
    except Exception as e:
        print(e)
        window.write_event_value('-THREAD_ERROR-', str(e))


def thread_list_process(operationList, window):
    globals.CANCEL_OPERATION = False
    mangas = ''

    if not ISTEST:
        window.write_event_value('-THREAD_LOG-', PrintLog("Iniciando a lista de operações com " + str(len(operationList)) + " operações...", 'magenta'))
    else:
        print(colored("Iniciando a lista de operações com " + str(len(operationList)) + " operações...", 'magenta', attrs=['reverse', 'blink']))

    try:
        for item in operationList:
            global OPERATION # Usa a variavel global
            OPERATION = item[0]
            initialMangaTime = datetime.now()
            if not ISTEST:
                window.write_event_value('-THREAD_LOG-', PrintLog("Inicio do processo do manga " + OPERATION.nameManga + " da lista de operações.", 'magenta'))
                window.write_event_value('-THREAD_LOG-', PrintLog('Inicio do processo: ' + initialMangaTime.strftime("%H:%M:%S"), 'magenta'))
            else:
                print(colored("Inicio do processo do manga " + OPERATION.nameManga + " da lista de operações.", 'magenta', attrs=['reverse', 'blink']))
                print(colored('Inicio do processo: ' + initialMangaTime.strftime("%H:%M:%S"), 'yellow', attrs=['reverse', 'blink']))

            process(OPERATION)

            if not globals.CANCEL_OPERATION:
                mangas += OPERATION.nameManga + ', '
                item[-1] = 'X'
                intervalManga = datetime.now() - initialMangaTime
                if not ISTEST:
                    window.write_event_value('-THREAD_LOG-', PrintLog("Manga processado com exito.... " + OPERATION.nameManga, 'magenta'))
                    window.write_event_value('-THREAD_LOG-', PrintLog('Fim do processo: ' + datetime.now().strftime("%H:%M:%S"), 'yellow'))
                    window.write_event_value('-THREAD_LOG-', PrintLog('Tempo decorrido: ' + str(intervalManga), 'yellow'))
                    window.write_event_value('-THREAD_LOG-', PrintLog(100*'-'))
                    window.write_event_value('-THREAD_LIST_UPDATE-', operationList)
                else:
                    print(colored("Manga processado com exito.... " + OPERATION.nameManga, 'magenta', attrs=['reverse', 'blink']))
                    print(colored('Fim do processo: ' + datetime.now().strftime("%H:%M:%S"), 'yellow', attrs=['reverse', 'blink']))
                    print(colored('Tempo decorrido: ' + str(intervalManga), 'yellow', attrs=['reverse', 'blink']))
                    print(100*'-')
        
        if not globals.CANCEL_OPERATION:    
            mangas = mangas[:mangas.rindex(", ")]

        window.write_event_value('-THREAD_END-', 'Processamento da lista concluído com sucesso. \nMangas processados: ' + mangas) 
    except Exception as e:
        print(e)
        window.write_event_value('-THREAD_ERROR-', str(e)) 


def thread_copy_file(operation, fromFolder, toFolder, folderName):
    globals.CANCEL_OPERATION = False
    try:
        if not operation.isTest:
            operation.window.write_event_value('-THREAD_LOG-', PrintLog("Iniciando a cópia dos arquivos de " + fromFolder + " para " + toFolder, 'yellow'))
        else:
            printLog(PrintLog("Iniciando a cópia dos arquivos de " + fromFolder + " para " + toFolder, 'yellow'))

        moveFilesDirectories(operation, fromFolder, toFolder, folderName)
        window.write_event_value('-THREAD_END-', ('Montagem da estrutura e cópia dos arquivos concluído com sucesso.\n' + folderName))
    except Exception as e:
        print(e)
        window.write_event_value('-THREAD_ERROR-', str(e))


def eventManga(values):
    base = values["-BASE-"]
    manga = values["-MANGA-"]
    language = acronymLanguage(values["-LANGUAGE-"])
    findLastVolume(base, manga, language)


def eventDirectory(values):
    global LAST_DIRECTORY
    directory = values["-DIRECTORY-"]

    if (LAST_DIRECTORY != directory and os.path.exists(directory)):
        window['-LABELBASE-'].Update('Base', text_color='white')
        LAST_DIRECTORY = directory
        config = readConfig(directory)

        if config is not None and directory == config.directory:            
            window['-MANGA-'].Update(config.manga)
            window['-VOLUME-'].Update(config.volume)
            window['-CHAPTER-'].Update(config.chapter)
            window['-SCAN-'].Update(config.scan)
            window['-BASE-'].Update(config.base)
            window['-LANGUAGE-'].Update(config.language)
            window['-OCRTYPE-'].Update(config.ocr)
            window['-GET_INFORMATION-'].Update(config.getFolderInformation)
            window['-GET_NAME-'].Update(config.getNameFolder)
            window['-FURIGANA-'].Update(config.isCleanFurigana)
            window['-ADDITIONAL_FILTER_FURIGANA-'].Update(config.isFuriganaFilter)
            window['-LABELBASE-'].Update('Base', text_color='chartreuse')

            if "japonês" not in config.language.lower():
                window['-FURIGANA-'].update(value=False, disabled=True)
                window['-ADDITIONAL_FILTER_FURIGANA-'].update(value=False, disabled=True)
            else:
                window['-FURIGANA-'].update(disabled=False)  
                window['-ADDITIONAL_FILTER_FURIGANA-'].update(disabled=False) 

            print(colored(f'Load config.', 'blue', attrs=['reverse', 'blink']))
            findLastVolume(config.base, config.manga, acronymLanguage(config.language))
        else:
            manga = values["-MANGA-"]
            language = acronymLanguage(values["-LANGUAGE-"])
            folder = ""

            for _, subFolder, _ in os.walk(directory):
                subFolder[:] = [sub for sub in subFolder if sub not in ['tmp']]
                subFolder[:] = [sub for sub in subFolder if "capa" not in sub.lower()]

                if len(subFolder) < 1:
                    return
                    
                folder = subFolder[0]
                manga = getDirectoryName(folder)
                chapter = getDirectoryInformation(folder, manga)
                break

            window['-MANGA-'].Update(manga)
            window['-VOLUME-'].Update(chapter.volume)
            window['-CHAPTER-'].Update(chapter.chapter)
            window['-SCAN-'].Update(chapter.scan)

            try:
                base = unidecode(manga.replace("-", " "))[:40].strip().lower()
                if base is not None and base != "":
                    find = False
                    words = base.split()
                    base = ""
                    table = None
                    for word in words:
                        if base == "":
                            base = word
                        else:
                            base = base + "_" + word
                        table = findTable(base, manga, language)
                        if table.exists:
                            find = True
                            break

                    window['-BASE-'].Update(base)
                    if find:
                        print(colored(f'Tabela com nome "{base}" encontrado.', 'green', attrs=['reverse', 'blink']))
                        window['-LABELBASE-'].Update('Base', text_color='chartreuse')
                    else:
                        print(colored(f'Não encontrado tabela, criação de nova tabela com nome "{base}".', 'yellow', attrs=['reverse', 'blink']))
                        window['-LABELBASE-'].Update('Base', text_color='orangered')

                    if table is not None:
                        print(colored(f'Último volume: ' + table.lastVolume, 'yellow', attrs=['reverse', 'blink']))
                        window['-LASTVOLUME-'].Update(table.lastVolume[:48])

                else:
                    window['-BASE-'].Update(unidecode(manga.replace("-", " "))[:40].strip())
                    window['-LABELBASE-'].Update('Base', text_color='orangered')
                    window['-LASTVOLUME-'].Update('')
            except Exception as e:
                print(colored(f'Erro na busca da tabela.', 'red', attrs=['reverse', 'blink'])) 
                print(colored(f"{str(e)}", 'red', attrs=['reverse', 'blink'])) 
                window['-BASE-'].Update(unidecode(manga.replace("-", " "))[:40].strip())
                window['-LABELBASE-'].Update('Base', text_color='orangered')
                window['-LASTVOLUME-'].Update('')

def eventFindLastVolume(values):
    base = values["-BASE-"]
    manga = values["-MANGA-"]
    language = acronymLanguage(values["-LANGUAGE-"])
    findLastVolume(base, manga, language)


def findLastVolume(base, manga, language):
    lastVolume = ''

    if base is not None and base != "":
        table = findTable(base, manga, language)
        if table is not None:
            lastVolume = table.lastVolume
            print(colored(f'Último volume: ' + table.lastVolume, 'yellow', attrs=['reverse', 'blink']))

    window['-LASTVOLUME-'].Update(lastVolume[:48])


def main():
    if ISTEST:
        teste()
    else:
        global OPERATION, SELECTED_ROW
        MaxProgress = 1
        initialTime = datetime.now()
        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED or event == '-BTN_CANCEL-':
                break
            elif event == '-DIRECTORY-':
                eventDirectory(values)
            elif event == '-MANGA-':
                eventManga(values)
            elif event == '-BASE-':
                eventFindLastVolume(values)
            elif event == '-TABLE-':
                SELECTED_ROW = values['-TABLE-']
            elif event == '-LANGUAGE-':
                if "japonês" not in values['-LANGUAGE-'].lower():
                   window['-FURIGANA-'].update(value=False, disabled=True)
                   window['-ADDITIONAL_FILTER_FURIGANA-'].update(value=False, disabled=True)
                else:
                    window['-FURIGANA-'].update(disabled=False)  
                    window['-ADDITIONAL_FILTER_FURIGANA-'].update(disabled=False)
                eventFindLastVolume(values)
            elif event == '-BTN_INSERT-':
                SELECTED_ROW = []
                if validateFields(values):
                    operation = load(values)
                    listOperations.append([operation, operation.base, operation.nameManga, operation.directory, operation.furigana, operation.language, ' - '])
                    window['-TABLE-'].update(values=listOperations)
                    cleanFields()
            elif event == '-BTN_REMOVE-':
                if len(listOperations) > 0:
                    if (len(SELECTED_ROW) > 0):
                        listOperations.pop(SELECTED_ROW[0])
                    else:
                        listOperations.pop()
                    window['-TABLE-'].update(values=listOperations)
                SELECTED_ROW = []
            elif ((event == '-BTN_PROCESS-') or (event == '-BTN_PROCESS_LIST-') or (event == '-BTN_COPY_FILES-')) and (window[event].get_text() == 'Parar processamento'):
                globals.CANCEL_OPERATION = True
            elif (event == '-BTN_PROCESS-') or (event == '-BTN_PROCESS_LIST-') or (event == '-BTN_COPY_FILES-'):
                if not testConnection():
                    alert('Não foi possível conectar ao banco de dados')

                if event == '-BTN_COPY_FILES-':
                    disableButtons("COPIA ARQUIVOS")
                    OPERATION = Operation(None, "", "", "", window)
                    OPERATION.logMemo = LOGMEMO
                    OPERATION.directory = values['-TO_PATH-']
                    threading.Thread(target=thread_copy_file,args=(OPERATION, values['-FROM_PATH-'], values['-TO_PATH-'], values['-FOLDER_NAME-']),daemon=True).start()
                elif (event == '-BTN_PROCESS_LIST-'):
                    if len(listOperations) == 0:
                        alert('Nenhuma operação na lista.')
                    else:
                        disableButtons("LISTA")
                        initialTime = datetime.now()
                        LOGMEMO.Update('')
                        printLog(PrintLog('Inicio do processo: ' + initialTime.strftime("%H:%M:%S"), 'yellow', logMemo=LOGMEMO, directory=os.path.abspath('')))
                        threading.Thread(target=thread_list_process,args=(listOperations, window),daemon=True).start()
                elif validateFields(values):
                    disableButtons("OPERAÇÃO")
                    initialTime = datetime.now()
                    LOGMEMO.Update('')
                    OPERATION = load(values)
                    printLog(PrintLog('Inicio do processo: ' + initialTime.strftime("%H:%M:%S"), 'yellow', logMemo=LOGMEMO, directory=OPERATION.directory))
                    threading.Thread(target=thread_process,args=(OPERATION, window),daemon=True).start()
            elif event == '-THREAD_AVISO-':
                alert(values[event])
            elif event == '-THREAD_LOG-':
                prtLog = values[event]
                prtLog.logMemo = LOGMEMO
                prtLog.directory = OPERATION.directory 
                printLog(prtLog)
            elif event == '-THREAD_PROGRESSBAR_UPDATE-':
                PROGRESS.UpdateBar(values[event], MaxProgress)
            elif event == '-THREAD_PROGRESSBAR_MAX-':
                MaxProgress = values[event]
            elif event == '-THREAD_LIST_UPDATE-':
                window['-TABLE-'].update(values=values[event])
            elif event == '-THREAD_ERROR-':
                alert('Erro no processamento....\n' + values[event])
                enableButtons()
            elif event == '-THREAD_END-':
                if globals.CANCEL_OPERATION:
                    printLog(PrintLog('Operação cancelada...', 'yellow', logMemo=LOGMEMO, directory=OPERATION.directory))
                    alert('Processamento parado.')
                else:
                    PROGRESS.UpdateBar(MaxProgress, MaxProgress)
                    interval = datetime.now() - initialTime
                    printLog(PrintLog('Fim do processo: ' + datetime.now().strftime("%H:%M:%S"), 'yellow', logMemo=LOGMEMO, directory=OPERATION.directory))
                    printLog(PrintLog('Tempo decorrido: ' + str(interval), 'yellow', logMemo=LOGMEMO, directory=OPERATION.directory))
                    if OPERATION.furigana:
                        printLog(PrintLog('Com limpeza de furigana.', logMemo=LOGMEMO, directory=OPERATION.directory))
                    alert(values[event])
                enableButtons()

        window.close()


if __name__ == '__main__':
    main()
