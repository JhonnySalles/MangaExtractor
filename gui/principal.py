import PySimpleGUI as sg

sg.theme('Black')   # Cores
# Layout
layout = [  [sg.Text('Caminho das imagens',text_color='red',size =(15, 1)), sg.InputText(key='caminho')],
            [sg.Text('Manga',text_color='red',size =(15, 1)), sg.InputText(key='manga')],
            [sg.Text('Volume',size =(15, 1)), sg.InputText(key='volume')],
            [sg.Text('Capitulo',size =(15, 1)), sg.InputText(key='capitulo')],
            [sg.Text('Scan',size =(15, 1)), sg.InputText(key='scan')],
            [sg.Text('Base',size =(15, 1)), sg.InputText(key='base')],
            [sg.Text('Linguagem',size =(15, 1)),sg.Combo(['Português','Japonês','Inglês'],default_value='Português',key='linguagem',size =(15, 1))],
            [sg.Button('Ok',size =(25, 1)), sg.Button('Cancel',size =(25, 1))] ]

# Create the Window
window = sg.Window('Manga Text Extractor', layout)

def validaCampos(values):
    return not ((values['caminho'].strip() == '') or (values['manga'].strip() == ''))

def aviso(text):
    sg.Popup(text,title='Aviso')

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
        break
    elif validaCampos(values):
        print('processando')
    else:
        aviso('Favor verificar os campos')

window.close()