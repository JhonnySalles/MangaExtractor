import os
import threading
import PySimpleGUI as sg
import sys

from PySimpleGUI.PySimpleGUI import ConvertArgsToSingleString
sys.path.append("./banco/")

from processa import ImageProcess
from classes import Operacao
from banco.bdUtil import BdUtil, testaConexao

###################################################
#Simular um teste sem abrir a janela
isTeste = False

def teste(window):
    operacao = Operacao(window, "b", "F:/Novapasta", "ja")
    operacao.ocrType = 'tesseract'
    operacao.isTeste = isTeste 

    db = BdUtil(operacao)
    operacao.base = db.criaTabela(operacao.base)

    processa = ImageProcess(operacao)
    processa.processaImagens()

#################################################
sg.theme('Black')   # Cores
# Layout
layout = [  [sg.Text('Caminho',text_color='orangered',size =(15, 1)), sg.Input(key='caminho', enable_events=True), sg.FolderBrowse('Selecionar pasta') ],
            [sg.Text('Manga',text_color='orangered',size =(15, 1)), sg.InputText(key='manga')],
            [sg.Text('Volume',size =(15, 1)), sg.InputText(key='volume')],
            [sg.Text('Capitulo',size =(15, 1)), sg.InputText(key='capitulo')],
            [sg.Text('Scan',size =(15, 1)), sg.InputText(key='scan')],
            [sg.Text('Base',size =(15, 1)), sg.InputText(key='base')],
            [sg.Text('Caminho Tesseract', text_color='cornflowerblue',size =(15, 1)), sg.Input(key='tesseract', default_text='C:/Program Files/Tesseract-OCR'), sg.FolderBrowse('Selecionar pasta')],
            [sg.Text('Linguagem',size =(15, 1)),sg.Combo(['Português','Japonês','Inglês'],default_value='Português',key='linguagem',size =(15, 1))],
            [sg.Text('Recurso OCR',size =(15, 1)),sg.Combo(['WinOCR','Tesseract'],default_value='Tesseract',key='ocrtype',size =(15, 1))],
            [sg.Checkbox('Carregar Informações da pasta', default=True, key="pasta")],
            [sg.Multiline(size=(80,10), key='-OUTPUT-')],
            [sg.ProgressBar(1000, orientation='h', size=(41, 5), key='progressbar')],
            [sg.Button('Ok',size =(30, 1)), sg.Text('',size =(7, 1)), sg.Button('Cancel',size =(30, 1))] ]

# Create the Window
window = sg.Window('Manga Text Extractor', layout)
progress = window['progressbar']
logMemo = window['-OUTPUT-']

def validaCampos(values):

    if values['ocrtype'].lower() == 'tesseract':
        file = ''.join(values['tesseract'].strip()).replace('\\', '/').replace('//', '/').replace('tesseract.exe', '')
        if (values['tesseract'].strip() == '') or (not os.path.isfile(file + '/tesseract.exe')):
            aviso('Tesseract não encontrado, favor verificar o caminho informado!')
            return False

    if ((values['caminho'].strip() == '') or (values['manga'].strip() == '')):
        aviso('Favor verificar os campos obrigatórios!')
        return False

    return True

def aviso(text):
    sg.Popup(text,title='Aviso')

def carrega(values):

    linguagem = ""
    if (values['manga'] == 'Japonês'):
        linguagem = "ja"
    elif (values['manga'] == 'Inglês'):
        linguagem = "en"
    else:
        linguagem = "pt"

    operacao = Operacao(window, values['manga'], values['caminho'], linguagem)
        
    operacao.volume = values['volume']
    operacao.capitulo = values['capitulo']
    operacao.scan = values['scan']
    operacao.isFolder = values['pasta']
    operacao.ocrType = values['ocrtype'].lower()
    operacao.pastaTesseract = ''.join(values['tesseract'].strip()).replace('\\', '/').replace('//', '/').replace('tesseract.exe', '')

    if values['base'].strip() != "": 
        operacao.base = values['base']

    return operacao

def processar(values):
    operacao = carrega(values)
    
    db = BdUtil(operacao)
    operacao.base = db.criaTabela(operacao.base)

    processa = ImageProcess(operacao)
    processa.processaImagens()

def thread_process():
    processar(values)
    aviso('Processamento concluido.')

def extraiInformacoesDiretorio(values):
    caminho = values["caminho"]

    if (os.path.exists(caminho)):
        caminho = values["caminho"]
        manga = values["manga"]
        scan = values['scan']
        pasta = ""

        for diretorio, subpastas, arquivos in os.walk(caminho):
            if "tmp" in subpastas: #Ignora as pastas temporárias da busca
                subpastas.remove("tmp")
                continue

            pasta = os.path.basename(diretorio)
            if ("[JPN]" in pasta.upper()) or ("[JAP]" in pasta.upper()):
                pasta = pasta.replace("[JAP]", "").replace("[JPN]", "")
                scan = ""
            elif "[" in pasta:
                scan = pasta[pasta.index("["):pasta.index("]")]
                scan = scan.replace("[","").replace("]","").strip()
                pasta = pasta.replace("[", "").replace("]", "").replace(scan, "").strip()

            if ("volume" in pasta.lower()):
                pasta = pasta[:pasta.lower().index("volume")]
            elif ("capitulo" in pasta.lower()):
                pasta = pasta[:pasta.lower().index("capitulo")]
            elif ("capítulo" in pasta.lower()):
                pasta = pasta[:pasta.lower().index("capítulo")]

            pasta = pasta.replace(" - ", "").strip()
            manga = pasta
            break

        window['caminho'].Update(caminho)
        window['manga'].Update(manga)
        window['scan'].Update(scan)

if isTeste:
    teste(None)
else:
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            break
        elif event == 'caminho':
            extraiInformacoesDiretorio(values)
        elif event == 'Ok':
            if not testaConexao():
                aviso('Não foi possível conectar ao banco de dados')
            elif validaCampos(values):
                threading.Thread(target=thread_process, daemon=True).start()
        
    window.close()