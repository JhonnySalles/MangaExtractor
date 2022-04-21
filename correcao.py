import os
import hashlib
from termcolor import colored
import re
from banco.bd import conection
from defaults import BD_NAME
from unidecode import unidecode
from PIL import Image
from mysql.connector.errors import ProgrammingError


def getDirectoryName(directory):
    folder = os.path.basename(directory)  # Obtem o name da folder

    if ("[JPN]" in folder.upper()) or ("[JAP]" in folder.upper()) or ("[JNP]" in folder.upper()):
        folder = folder.replace("[JPN]", "").replace("[JAP]", "").replace("[JNP]", "")
    elif "[" in folder:
        scan = folder[folder.index("["):folder.index("]")]
        folder = folder.replace(scan, "").replace("[", "").replace("]", "")

    folder = folder.replace(" - ", " ")

    if ("volume" in folder.lower()):
        folder = folder[:folder.lower().rindex("volume")]
    elif ("capítulo" in folder.lower()):
        folder = folder[:folder.lower().rindex("capítulo")]
    elif ("capitulo" in folder.lower()):
        folder = folder[:folder.lower().rindex("capitulo")]

    return folder.replace("  ", " ").strip()

class CorrectionPage:
    def __init__(self, table, manga, volume, chapter):
        pass
        self.table = manga if table is None else table
        self.table = unidecode(self.table.replace("-", " "))[:40].strip()
        self.manga = manga
        self.volume = volume
        self.chapter = chapter
        self.language = ""
        self.pageName = ""
        self.pageNumber = ""
        self.hashPage = ""
        self.hashOldPage = ""
        self.isExtra = False


selectChapter = """
    SELECT id, manga, volume, capitulo, linguagem FROM {}_capitulos
    WHERE manga = %s AND volume = %s AND capitulo = %s AND linguagem = %s AND is_extra = %s
"""

correctionMd5Image = """
    UPDATE {}_paginas SET hash_pagina = %s
    WHERE id_capitulo = %s AND (nome = %s or hash_pagina = %s) 
"""

tableExists = """
    SELECT Table_Name FROM information_schema.tables 
    WHERE table_schema = "%s" 
    AND (Table_Name LIKE "%s_textos")
    GROUP BY Table_Name
"""

def saveFile(log):
    with open(os.path.abspath('') + '/sql_nao_processado.log', 'a+', encoding='utf-8') as file:
        file.write(''.join(log).replace("\n", "") + '\n')

def listCorrection(description):
    with open(os.path.abspath('') + '/listaCorrecao.log', 'a+', encoding='utf-8') as file:
        file.write(description + '\n')

def generateSqlFile(table, correction, idChapter, information):
    sql = selectChapter.format(table) % ('"'+correction.manga+'"', correction.volume, correction.chapter, '"'+correction.language+'"', correction.isExtra)
    saveFile(information + " --- " + correction.manga + ' - vol: ' + correction.volume + ' cap: ' + correction.chapter + " --- 1 - "  + sql )

    sql = correctionMd5Image.format(table) % ('"'+correction.hashPage+'"', idChapter, '"'+correction.pageName+'"', '"'+correction.hashOldPage+'"')
    saveFile(information + " --- " + correction.manga + ' - vol: ' + correction.volume + ' cap: ' + correction.chapter + " --- 2 - " + sql)


def updatePage(correction):
    with conection() as connection:

        file = False
        table = correction.table.replace(" ", "_")
        try:
            cursor = connection.cursor(buffered=True)
            cursor.execute(tableExists % (BD_NAME, table))

            if cursor.rowcount <= 0:
                file = True
        except ProgrammingError as e:
            print(colored(f'Erro na verificação da tabela: {e.msg}', 'red', attrs=['reverse', 'blink']))
            return

        if file:
            generateSqlFile(table, correction, "!000", " - não encontrado tabela")
        else:
            idChapter = 0
            try:
                args = (correction.manga, correction.volume, correction.chapter, correction.language, correction.isExtra)
                cursor = connection.cursor(buffered=True)
                sql = selectChapter.format(table)
                cursor.execute(sql, args)

                if cursor.rowcount <= 0:
                    generateSqlFile(table, correction, "$000", " - não encontrado capitulo")
                    return
                else:
                    row = cursor.next()
                    idChapter = row[0]

            except ProgrammingError as e:
                print(colored(f'Erro na obtenção do capitulo: {e.msg}', 'red', attrs=['reverse', 'blink']))

            try:
                cursor = connection.cursor()
                args = (correction.hashPage, idChapter, correction.pageName, correction.hashOldPage)
                sql = correctionMd5Image.format(table)
                cursor.execute(sql, args)
                connection.commit()
                if cursor.rowcount <= 0:
                    generateSqlFile(table, correction, idChapter, " - nenhum registro atualizado no update")
                else:
                    listCorrection(correction.language + ' - ' + correction.manga + ' - vol: ' + correction.volume + ' cap: ' + correction.chapter)
            except ProgrammingError as e:
                print(colored(f'Erro ao realizar o update do md5: {e.msg}', 'red', attrs=['reverse', 'blink']))

                    
class Correction:
    def __init__(self, table, language, directory, isExtra):
        pass

        # Caminhos temporários
        self.language = language
        self.directory = ''.join(directory + "/").replace("//", "/")
        self.table = table
        self.isExtra = isExtra

    def generateClassCorrectionPage(self, directory):
        folder = os.path.basename(directory)  # Pasta que está
        folder = folder.lower()

        volume = '0'
        chapter = '0'
        if ("capítulo" in folder) or ("capitulo" in folder) or (("extra" in folder) and (folder.rindex("volume") < folder.rindex("extra"))):
            if "capítulo" in folder:
                volume = folder[folder.rindex("volume"):folder.rindex("capítulo")]
                volume = volume.replace("volume", "").replace("-", "").strip()

                chapter = folder[folder.rindex("capítulo"):]
                chapter = chapter.replace("capítulo", "").strip()
            elif "capitulo" in folder:
                volume = folder[folder.rindex("volume"):folder.rindex("capitulo")]
                volume = volume.replace("volume", "").replace("-", "").strip()

                chapter = folder[folder.rindex("capitulo"):]
                chapter = chapter.replace("capitulo", "").strip()
            elif "extra" in folder:
                volume = folder[folder.rindex("volume"):folder.rindex("extra")]
                volume = volume.replace("volume", "").replace("-", "").strip()

                chapter = folder[folder.rindex("extra"):]
                chapter = chapter.replace("extra", "").strip()

            volume = re.sub('\D', '', volume)
            chapter = re.sub('\D', '', chapter)

            if volume == "":
                volume = '0'

            if chapter == "":
                chapter = '0'

        obj = CorrectionPage(self.table, getDirectoryName(directory), volume, chapter)
        obj.language = self.language
        obj.isExtra = self.isExtra

        return obj

    def fixMD5(self):
        pages = []
        print(colored("Inicio da correção dos MD5...", 'green', attrs=['reverse', 'blink']))
        for directory, subFolder, files in os.walk(self.directory):
            # Ignora as pastas temporárias da busca
            subFolder[:] = [sub for sub in subFolder if sub not in ['tmp']]
            # Ignora as pastas de capa
            subFolder[:] = [sub for sub in subFolder if "capa" not in sub.lower()]

            if len(files) <= 0:
                continue

            pageNumber = 0
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    pageNumber += 1
                    page = self.generateClassCorrectionPage(directory)
                    md5hash = hashlib.md5()
                    with open(os.path.join(directory, file),'rb') as f:
                        line = f.read()
                        md5hash.update(line)
                    page.hashPage = md5hash.hexdigest()

                    try:
                        md5hashOld = hashlib.md5(Image.open(os.path.join(directory, file)).tobytes())
                        page.hashOldPage = md5hashOld.hexdigest()
                    except ProgrammingError as e:
                        print(colored(f'Erro ao carregar hash antigo: {e.msg}', 'red', attrs=['reverse', 'blink']))

                    page.pageName = file
                    pages.append(page)
                    print(os.path.join(directory, file))

        print(colored("Atualizando as paginas...", 'green', attrs=['reverse', 'blink']))
        for page in pages:
            print(colored("Atualizando MD5: " + page.manga + " - vol: " + page.volume + " cap: " + page.chapter + " - " + page.pageName, 'green', attrs=['reverse', 'blink']))
            updatePage(page)
        print(colored("Concluido. " + self.directory, 'green', attrs=['reverse', 'blink']))

            
if __name__ == '__main__':
    correction = Correction(None, "ja", "G:/reprocessando/aa obter pelo nome", False)
    correction.fixMD5()

   
