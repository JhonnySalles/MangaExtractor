import os

from banco_dados.criar_tabela import criaTabela

def extraiInformacoes(diretorio):
    pasta = os.path.basename(diretorio) # Pasta que está

    if "[" in pasta:
        scan = pasta[pasta.index("["):pasta.index("]")]
        scan = scan.replace("[","").replace("]","").strip()
        isScan = bool(scan) # Caso a scan seja vazia será falso
    else:
        scan = ""
        isScan = bool("FALSE")

    pasta = pasta.lower()
    volume = pasta[pasta.index("volume"):pasta.index("-", pasta.index("volume"))]
    volume = volume.replace("volume", "").strip()

    if "capítulo" in pasta:
        capitulo = pasta[pasta.index("capítulo"):]
        capitulo = capitulo.replace("capítulo", "").strip()
    else:
        capitulo = pasta[pasta.index("capitulo"):]
        capitulo = capitulo.replace("capitulo", "").strip()

    return volume, capitulo, scan, isScan

tabela = ''
def percorreDiretorio(caminho=None, manga=None, linguagem=None):
    if caminho.strip() == None:
        raise ValueError("Caminho da pasta não informada.")
    if manga.strip() == None:
        raise ValueError("Nome do manga não informado.")

    try:
        tabela = criaTabela(manga)
    except:
        print('Tabela ' + tabela + ' já existente')

    for diretorio, subpastas, arquivos in os.walk(caminho):
        for arquivo in arquivos:
            if arquivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                print(os.path.join(diretorio, arquivo)) # Caminho completo
                informacoes = extraiInformacoes(diretorio)
                texto = ''


percorreDiretorio('F:/Novapasta', 'Teste 1', 'JP')
