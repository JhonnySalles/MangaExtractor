import PySimpleGUI as sg
import sys
sys.path.append("./banco/")

from processa import ImageProcess
from classes import Operacao
from banco.bdUtil import testaConexao, criaTabela, gravarDados

###################################################
#Simular um teste sem abrir a janela
isTeste = True

def teste():
    operacao = Operacao("a", "F:/Novapasta", "pt")
        
    operacao.volume = ""
    operacao.capitulo = ""
    operacao.scan = ""
    operacao.base = "a"
    operacao.isFolder = True # Define que deve carregar as informações da pasta

    operacao.base = criaTabela(operacao.base)

    processa = ImageProcess(operacao)
    processados = processa.processaImagens()
    gravarDados(operacao, processados)

#################################################
sg.theme('Black')   # Cores
# Layout
layout = [  [sg.Text('Caminho',text_color='red',size =(15, 1)), sg.Input(key='caminho')],
            [sg.Text('Manga',text_color='red',size =(15, 1)), sg.InputText(key='manga')],
            [sg.Text('Volume',size =(15, 1)), sg.InputText(key='volume')],
            [sg.Text('Capitulo',size =(15, 1)), sg.InputText(key='capitulo')],
            [sg.Text('Scan',size =(15, 1)), sg.InputText(key='scan')],
            [sg.Text('Base',size =(15, 1)), sg.InputText(key='base')],
            [sg.Text('Linguagem',size =(15, 1)),sg.Combo(['Português','Japonês','Inglês'],default_value='Português',key='linguagem',size =(15, 1))],
            [sg.Checkbox('Carregar Informações da pasta', default=True, key="pasta")],
            #[sg.Output(size=(70,10), key='-OUTPUT-')],
            [sg.Button('Ok',size =(30, 1)), sg.Button('Cancel',size =(30, 1))] ]

# Create the Window
window = sg.Window('Manga Text Extractor', layout)

def validaCampos(values):
    return not ((values['caminho'].strip() == '') or (values['manga'].strip() == ''))

def aviso(text):
    sg.Popup(text,title='Aviso')

def carrega(values):

    linguagem = ""
    if (values['manga'] == 'Japonês'):
        linguagem = "jp"
    elif (values['manga'] == 'Inglês'):
        linguagem = "en"
    else:
        linguagem = "pt"

    operacao = Operacao(values['manga'], values['caminho'], linguagem)
        
    operacao.volume = values['volume']
    operacao.capitulo = values['capitulo']
    operacao.scan = values['scan']
    operacao.base = values['base']
    operacao.isFolder = values['pasta']

    if operacao.base .strip() == "": 
        operacao.base = values['manga']

    return operacao


def processar(values):
    if not testaConexao():
        aviso('Não foi possível conectar ao banco de dados')
        return

    operacao = carrega(values)
    operacao.base = criaTabela(operacao.base)

    processa = ImageProcess(operacao)
    processados = processa.processaImagens()
    gravarDados(operacao, processados)


if isTeste:
    teste()
else:
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            break
        elif validaCampos(values):
            processar(values)
        else:
            aviso('Favor verificar os campos')

    window.close()