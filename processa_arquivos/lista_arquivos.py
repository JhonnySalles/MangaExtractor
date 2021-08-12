import os

def percorreDiretorio(caminho='', manga='', linguagem=''):
    if caminho.strip() == '':
        raise ValueError("Caminho da pasta não informada.")

    for diretorio, subpastas, arquivos in os.walk(caminho):
        for arquivo in arquivos:
            if arquivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                print(os.path.join(diretorio, arquivo)) # Caminho completo
                # print(arquivo) # Nome do arquivo

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

                print("volume: " + volume + " - capítulo: " + capitulo + " - scan: " + scan)
