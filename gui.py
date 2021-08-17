import os
import threading
import PySimpleGUI as sg
import sys

from PySimpleGUI.PySimpleGUI import ConvertArgsToSingleString
sys.path.append("./banco/")

from processa import ImageProcess, extraiNomeDiretorio
from classes import Operacao
from banco.bdUtil import BdUtil, testaConexao

###################################################
#Simular um teste sem abrir a janela
isTeste = False

def teste(window):
    operacao = Operacao(window, "teste",  "teste", "F:/Novapasta", "ja")
    operacao.ocrType = 'tesseract'
    operacao.isTeste = isTeste 

    db = BdUtil(operacao)
    operacao.base = db.criaTabela(operacao.base)

    processa = ImageProcess(operacao)
    processa.processaImagens()

#################################################
sg.theme('Black')   # Cores
# Layout
layout = [  [sg.Text('Caminho', text_color='orangered', size =(15, 1)), sg.Input(key='caminho', enable_events=True, default_text='C:/'), sg.FolderBrowse('Selecionar pasta') ],
            [sg.Text('Nome Manga', text_color='cornflowerblue', size =(15, 1)), sg.Input(key='manga', enable_events=True)],
            [sg.Checkbox('Obter o nome do manga da pasta?', default=False, key="get_nome")],
            [sg.Text('Volume',size =(15, 1)), sg.InputText(key='volume')],
            [sg.Text('Capitulo',size =(15, 1)), sg.InputText(key='capitulo')],
            [sg.Text('Scan',size =(15, 1)), sg.InputText(key='scan')],
            [sg.Text('Base', text_color='orangered', size =(15, 1)), sg.InputText(key='base')],
            [sg.Text('Caminho Tesseract', text_color='cornflowerblue',size =(15, 1)), sg.Input(key='tesseract', default_text='C:/Program Files/Tesseract-OCR'), sg.FolderBrowse('Selecionar pasta')],
            [sg.Text('Linguagem',size =(15, 1)),sg.Combo(['Português','Japonês','Inglês','Japonês (vertical)','Japonês (horizontal)'],default_value='Japonês',key='linguagem',size =(15, 1))],
            [sg.Text('Recurso OCR',size =(15, 1)),sg.Combo(['WinOCR','Tesseract'], default_value='Tesseract', key='ocrtype',size =(15, 1))],
            [sg.Checkbox('Carregar Informações da pasta?', default=True, key="get_informacao")],
            [sg.Multiline(size=(80,10), key='-OUTPUT-')],
            [sg.ProgressBar(100, orientation='h', size=(41, 5), key='progressbar')],
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

    if (values['caminho'].strip() == ''):
        aviso('Favor informar um caminho de origem!')
        return False
    elif not os.path.exists(''.join(values['caminho']).replace('\\', '/').replace('//', '/')):
        aviso('Caminho informado não encontrado!')
        return False

    if (values['manga'].strip() == '') and ((not values['get_nome']) or (values['get_informacao'])):
        aviso('Favor informar um nome!')
        return False

    if (values['base'].strip() == ''):
        aviso('Favor informar uma base!')
        return False

    return True

def aviso(text):
    sg.Popup(text,title='Aviso')

def carrega(values):

    vertical = None
    linguagem = ""
    if (values['linguagem'] == 'Japonês'):
        linguagem = "ja"
    elif (values['linguagem'] == 'Inglês'):
        linguagem = "en"
    elif (values['linguagem'] == 'Japonês (horizontal)'):
        linguagem = "ja"
        vertical = False
    elif (values['linguagem'] == 'Japonês (vertical)'):
        linguagem = "ja"
        vertical  = True
    else:
        linguagem = "pt"

    operacao = Operacao(window, values['base'], values['manga'], values['caminho'], linguagem)
        
    operacao.volume = values['volume']
    operacao.capitulo = values['capitulo']
    operacao.scan = values['scan']
    operacao.getNomePasta = values['get_nome']
    operacao.getInformacaoPasta = values['get_informacao']
    operacao.ocrType = values['ocrtype'].lower()
    operacao.pastaTesseract = ''.join(values['tesseract'].strip()).replace('\\', '/').replace('//', '/').replace('tesseract.exe', '')
    operacao.textoVertical = vertical

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

def eventoManga(values):
    window['base'].Update(values['manga'])

def extraiInformacoesDiretorio(values):
    caminho = values["caminho"]

    if (os.path.exists(caminho)):
        manga = values["manga"]
        pasta = ""

        for diretorio, subpastas, arquivos in os.walk(caminho):
            if "tmp" in subpastas: #Ignora as pastas temporárias da busca
                subpastas.remove("tmp")

            pasta = subpastas[0]
            manga = extraiNomeDiretorio(pasta)
            break

        window['manga'].Update(manga)
def main():
    if isTeste:
        teste(None)
    else:
        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
                break
            elif event == 'caminho':
                extraiInformacoesDiretorio(values)
            elif event == 'manga':
                eventoManga(values)
            elif event == 'Ok':
                if not testaConexao():
                    aviso('Não foi possível conectar ao banco de dados')
                elif validaCampos(values):
                    threading.Thread(target=thread_process, daemon=True).start()
            
        window.close()

if __name__ == '__main__':
  main()