import os
import hashlib
from termcolor import colored
import re
from banco.bd import conection
from defaults import NOME_DB
from mysql.connector.errors import ProgrammingError


def extraiNomeDiretorio(diretorio):
    pasta = os.path.basename(diretorio)  # Obtem o nome da pasta

    if ("[JPN]" in pasta.upper()) or ("[JAP]" in pasta.upper()) or ("[JNP]" in pasta.upper()):
        pasta = pasta.replace("[JPN]", "").replace("[JAP]", "").replace("[JNP]", "")
    elif "[" in pasta:
        scan = pasta[pasta.index("["):pasta.index("]")]
        pasta = pasta.replace(scan, "").replace("[", "").replace("]", "")

    pasta = pasta.replace(" - ", " ")

    if ("volume" in pasta.lower()):
        pasta = pasta[:pasta.lower().rindex("volume")]
    elif ("capítulo" in pasta.lower()):
        pasta = pasta[:pasta.lower().rindex("capítulo")]
    elif ("capitulo" in pasta.lower()):
        pasta = pasta[:pasta.lower().rindex("capitulo")]

    return pasta.replace("  ", " ").strip()

class CorrecaoPagina:
    def __init__(self, tabela, manga, volume, capitulo):
        pass
        self.tabela = manga if tabela is None else tabela
        self.manga = manga
        self.volume = volume
        self.capitulo = capitulo
        self.language = ""
        self.paginaNome = ""
        self.paginaNumero = ""
        self.hashPagina = ""
        self.isExtra = False


selectCapitulo = """
    SELECT id, manga, volume, capitulo, linguagem FROM {}_capitulos
    WHERE manga = %s AND volume = %s AND capitulo = %s AND linguagem = %s AND is_extra = %s
"""

correcaoMd5Image = """
    UPDATE {}_paginas SET hash_pagina = %s
    WHERE nome = %s AND id_capitulo = %s
"""

tabelaExist = """
    SELECT Table_Name FROM information_schema.tables 
    WHERE table_schema = "%s" 
    AND (Table_Name LIKE "%s_textos")
    GROUP BY Table_Name
"""

def salvaArquivo(log):
    with open(os.path.abspath('') + '/correcao.log', 'a+', encoding='utf-8') as file:
        file.write(''.join(log).replace("\n", "") + '\n')

def listaCorrecao(descricao):
    with open(os.path.abspath('') + '/listaCorrecao.log', 'a+', encoding='utf-8') as file:
        file.write(descricao + '\n')

def updatePagina(correcao):
    with conection() as conexao:

        arquivo = False
        tabela = correcao.tabela.replace(" ", "_")
        try:
            cursor = conexao.cursor(buffered=True)
            cursor.execute(tabelaExist % (NOME_DB, tabela))

            if cursor.rowcount <= 0:
                arquivo = True
        except ProgrammingError as e:
            print(colored(f'Erro na verificação da tabela: {e.msg}', 'red', attrs=['reverse', 'blink']))
            return

        if arquivo:
            sql = correcaoMd5Image.format(tabela) % (correcao.hashPagina, correcao.paginaNome, "00000")
            salvaArquivo(sql)
        else:
            idCapitulo = 0
            try:
                args = (correcao.manga, correcao.volume, correcao.capitulo, correcao.language, correcao.isExtra)
                cursor = conexao.cursor(buffered=True)
                sql = selectCapitulo.format(tabela)
                cursor.execute(sql, args)

                if cursor.rowcount <= 0:
                    sql = selectCapitulo.format(tabela) % ('"'+correcao.manga+'"', correcao.volume, correcao.capitulo, '"'+correcao.language+'"', correcao.isExtra)
                    salvaArquivo(sql + " --- " + correcao.manga + ' - vol: ' + correcao.volume + ' cap: ' + correcao.capitulo + " - não encontrado capitulo")
                    return
                else:
                    row = cursor.next()
                    idCapitulo = row[0]

            except ProgrammingError as e:
                print(colored(f'Erro na obtenção do capitulo: {e.msg}', 'red', attrs=['reverse', 'blink']))

            try:
                cursor = conexao.cursor()
                args = (correcao.hashPagina, correcao.paginaNome, idCapitulo)
                sql = correcaoMd5Image.format(tabela)
                cursor.execute(sql, args)
                conexao.commit()
                if cursor.rowcount <= 0:
                    sql = correcaoMd5Image.format(tabela) % ('"'+correcao.hashPagina+'"', '"'+correcao.paginaNome+'"', idCapitulo)
                    salvaArquivo(sql + " --- " + correcao.manga + ' - vol: ' + correcao.volume + ' cap: ' + correcao.capitulo + " - nenhum registro encontrado no update")
            except ProgrammingError as e:
                print(colored(f'Erro ao realizar o update do md5: {e.msg}', 'red', attrs=['reverse', 'blink']))
        
        listaCorrecao(correcao.language + ' - ' + correcao.manga + ' - vol: ' + correcao.volume + ' cap: ' + correcao.capitulo)

                    
class Correcao:
    def __init__(self, tabela, language, caminho, isExtra):
        pass

        # Caminhos temporários
        self.language = language
        self.caminho = ''.join(caminho + "/").replace("//", "/")
        self.tabela = tabela
        self.isExtra = isExtra

    def criaClasseCorrecaoPagina(self, diretorio):
        pasta = os.path.basename(diretorio)  # Pasta que está
        pasta = pasta.lower()

        volume = '0'
        capitulo = '0'
        if ("capítulo" in pasta) or ("capitulo" in pasta) or (("extra" in pasta) and (pasta.rindex("volume") < pasta.rindex("extra"))):
            if "capítulo" in pasta:
                volume = pasta[pasta.rindex("volume"):pasta.rindex("capítulo")]
                volume = volume.replace("volume", "").replace("-", "").strip()

                capitulo = pasta[pasta.rindex("capítulo"):]
                capitulo = capitulo.replace("capítulo", "").strip()
            elif "capitulo" in pasta:
                volume = pasta[pasta.rindex("volume"):pasta.rindex("capitulo")]
                volume = volume.replace("volume", "").replace("-", "").strip()

                capitulo = pasta[pasta.rindex("capitulo"):]
                capitulo = capitulo.replace("capitulo", "").strip()
            elif "extra" in pasta:
                volume = pasta[pasta.rindex("volume"):pasta.rindex("extra")]
                volume = volume.replace("volume", "").replace("-", "").strip()

                capitulo = pasta[pasta.rindex("extra"):]
                capitulo = capitulo.replace("extra", "").strip()

            volume = re.sub('\D', '', volume)
            capitulo = re.sub('\D', '', capitulo)

            if volume == "":
                volume = '0'

            if capitulo == "":
                capitulo = '0'

        obj = CorrecaoPagina(self.tabela, extraiNomeDiretorio(diretorio), volume, capitulo)
        obj.language = self.language
        obj.isExtra = self.isExtra

        return obj

    def corrigeMD5(self):
        paginas = []
        print(colored("Inicio da correção dos MD5...", 'green', attrs=['reverse', 'blink']))
        for diretorio, subpastas, arquivos in os.walk(self.caminho):
            # Ignora as pastas temporárias da busca
            subpastas[:] = [sub for sub in subpastas if sub not in ['tmp']]
            # Ignora as pastas de capa
            subpastas[:] = [sub for sub in subpastas if "capa" not in sub.lower()]

            if len(arquivos) <= 0:
                continue

            numeroPagina = 0
            for arquivo in arquivos:
                if arquivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                    numeroPagina += 1
                    pagina = self.criaClasseCorrecaoPagina(diretorio)
                    md5hash = hashlib.md5()
                    with open(os.path.join(diretorio, arquivo),'rb') as f:
                        line = f.read()
                        md5hash.update(line)
                    pagina.hashPagina = md5hash.hexdigest()
                    pagina.paginaNome = arquivo
                    paginas.append(pagina)
                    print(os.path.join(diretorio, arquivo))

        print(colored("Atualizando as paginas...", 'green', attrs=['reverse', 'blink']))
        for pagina in paginas:
            print(colored("Atualizando MD5: " + pagina.manga + " - vol: " + pagina.volume + " cap: " + pagina.capitulo + " - " + pagina.paginaNome, 'green', attrs=['reverse', 'blink']))
            updatePagina(pagina)
        print(colored("Concluido.", 'green', attrs=['reverse', 'blink']))

            
if __name__ == '__main__':
    correcao = Correcao("Sora no otoshimono", "ja", "G:/reprocessando", True)
    correcao.corrigeMD5()

