from mysql.connector.errors import ProgrammingError
from .bd import conection
from termcolor import colored
import sys
sys.path.append("../")
from classes import PrintLog, Volume
from util import printLog
from defaults import BD_NAME, APPLICATION_VERSION
import uuid
import os

tableVolumes = "_volumes"
tableChapters = "_capitulos"
tablePages = "_paginas"
tableText = "_textos"
tableVocabulary = "_vocabularios"
tableCover = "_capas"
tableCreate = """ CALL create_table('%s'); """

triggerInsert = """
CREATE
    TRIGGER tr_%s_insert BEFORE INSERT
    ON %s
    FOR EACH ROW BEGIN
	IF (NEW.id IS NULL OR NEW.id = '')  THEN
		SET new.id = UUID();
	END IF;
    END
"""

triggerUpdate = """
CREATE
    TRIGGER tr_%s_update BEFORE UPDATE
    ON %s
    FOR EACH ROW BEGIN
	    SET new.atualizacao = NOW();
    END
"""

selectVolume = 'SELECT id FROM {}_volumes WHERE manga = %s AND volume = %s AND linguagem = %s '
insertVolume = """
    INSERT INTO {}_volumes (id, manga, volume, linguagem) 
    VALUES (%s, %s, %s, %s)
"""
updateVolume = """
    UPDATE {}_volumes SET manga = %s, volume = %s, linguagem = %s
    WHERE id = %s
"""

selectChapter = 'SELECT id FROM {}_capitulos WHERE id_volume = %s AND manga = %s AND volume = %s AND capitulo = %s AND linguagem = %s AND is_extra = %s '
insertChapter = """
    INSERT INTO {}_capitulos (id, id_volume, manga, volume, capitulo, linguagem, scan, is_extra, is_raw) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""
updateChapter = """
    UPDATE {}_capitulos SET manga = %s, volume = %s, capitulo = %s, linguagem = %s, scan = %s, is_extra = %s, is_raw = %s
    WHERE id = %s
"""

selectPage = 'SELECT id FROM {}_paginas WHERE id_capitulo = %s AND nome = %s AND hash_pagina = %s '
insertPage = """
    INSERT INTO {}_paginas (id, id_capitulo, nome, numero, hash_pagina) 
    VALUES (%s, %s, %s, %s, %s)
"""
updatePage = """
    UPDATE {}_paginas SET nome = %s, numero = %s, hash_pagina = %s
    WHERE id = %s
"""

selectText = 'SELECT id FROM {}_textos WHERE id_pagina = %s AND texto = %s '
insertText = """
    INSERT INTO {}_textos (id, id_pagina, sequencia, texto, posicao_x1, posicao_y1, posicao_x2, posicao_y2, versao_app) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""
updateText = """
    UPDATE {}_textos SET sequencia = %s, texto = %s, posicao_x1 = %s, posicao_y1 = %s, posicao_x2 = %s, posicao_y2 = %s, versao_app = %s
    WHERE id = %s
"""

selectCover = 'SELECT id FROM {}_capas WHERE id_volume = "%s" '
insertCover = """
    INSERT INTO {}_capas (id, id_volume, manga, volume, linguagem, arquivo, extensao, capa) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""
updateCover = """
    UPDATE {}_capas SET manga = %s, volume = %s, linguagem = %s, arquivo = %s, extensao = %s, capa = %s
    WHERE id = %s
"""

tableExists = """
    SELECT Table_Name FROM information_schema.tables 
    WHERE table_schema = "%s" 
    AND (Table_Name LIKE "%s_textos")
    GROUP BY Table_Name
"""

selectLastVolume = """
    SELECT volume, manga FROM {}_volumes 
    WHERE linguagem = %s AND manga LIKE %s
    ORDER BY volume DESC LIMIT 1
"""

selectNextChapters = """
    SELECT Cap.ID AS ID FROM {}_capitulos AS reg 
    INNER JOIN {}_capitulos AS cap ON reg.id_volume = cap.id_volume AND (cap.capitulo >= reg.capitulo OR cap.is_extra = 1) 
    WHERE reg.id IN ("%s") 
    ORDER BY cap.is_Extra, cap.Capitulo
"""

deleteVocabularyPageFromChapter = """
    DELETE vol FROM {}_vocabularios AS vol 
    INNER JOIN {}_paginas AS p ON p.id = vol.id_pagina 
    INNER JOIN {}_capitulos AS c ON c.id = p.id_capitulo 
    WHERE c.id IN ("%s");
"""

deleteVocabularyChapterFromChapter = """
    DELETE vol FROM {}_vocabularios AS vol 
    INNER JOIN {}_capitulos AS c ON c.id = vol.id_capitulo 
    WHERE c.id IN ("%s");
"""

deleteTextsFromChapter = """ 
    DELETE t FROM {}_textos AS t 
    INNER JOIN {}_paginas AS p ON p.id = t.id_pagina 
    INNER JOIN {}_capitulos AS c ON c.id = p.id_capitulo 
    WHERE c.id IN ("%s");
"""

deletePagesFromChapter = """ 
    DELETE p FROM {}_paginas p 
    INNER JOIN {}_capitulos AS c ON c.id = p.id_capitulo 
    WHERE c.id IN ("%s");
"""

deleteChapter = """
    DELETE c FROM {}_capitulos AS c 
    WHERE c.id IN ("%s");
"""


class BdUtil:
    def __init__(self, operation):
        self.operation = operation
        self.table = ''


    def existTable(self, name=None):
        if name == None:
            raise ValueError("Tabela não informada.")

        find = False
        with conection() as connection:            
            try:
                table = name.replace(" ", "_")
                cursor = connection.cursor(buffered=True)
                cursor.execute(tableExists % (BD_NAME, table))
                find = cursor.rowcount > 0
            except ProgrammingError as e:
                print(colored(f'Erro na verificação de existência da tabela: {e.msg}', 'red', attrs=['reverse', 'blink']))
        return find
    

    def lastVolume(self, table, mangaName, language):
        register = 'Não foi possível conectar no banco.'
        with conection() as connection:   
            register = 'Não localizado último volume.'         
            try:
                args = (language, mangaName)
                sql = selectLastVolume.format(table)
                cursor = connection.cursor(buffered=True)
                cursor.execute(sql, args)
                if cursor.rowcount > 0:
                    result = cursor.fetchone()
                    register = 'Último volume ' + str(result[0]) + ' do manga ' + result[1] + '.'
                else:
                    register = 'Não há volume novo com o parâmetro informado.'
            except ProgrammingError as e:
                print(colored(f'Erro na verificação do último volume: {e.msg}', 'red', attrs=['reverse', 'blink']))
                register = 'Erro na verificação do último volume.'
            except Exception as e:
                print(colored(f'Erro na verificação do último volume: {str(e)}', 'red', attrs=['reverse', 'blink']))
                register = 'Erro na verificação do último volume.'
        return register


    def createTable(self, name=None):
        with conection() as connection:
            if name == None:
                raise ValueError("Erro na criação da tabela, tabela não informada.")

            table = name.replace(" ", "_")
            try:
                cursor = connection.cursor(buffered=True)
                cursor.execute(tableExists % (BD_NAME, table))

                if cursor.rowcount > 0:
                    cursor.close()
                    if not self.operation.isTest:
                        self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Estrutura de tabelas já existente. Tabela: {table}', 'red')) 
                    else:
                        print(colored(f'Estrutura de tabelas já existente. Tabela: {table}', 'red', attrs=['reverse', 'blink']))
                    self.table = table
                    return table
                
                cursor.close()
            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na criação das tabelas: {e.msg}', 'red')) 
                else:
                    print(colored(f'Erro na consulta da existencia da tabela volume: {e.msg}', 'red', attrs=['reverse', 'blink']))

            try:
                cursor = connection.cursor()
                cursor.execute(tableCreate % table)
                connection.commit()
                cursor.close()
            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na criação das tabelas: {e.msg}', 'red')) 
                else:
                    print(colored(f'Erro na criação das tabelas: {e.msg}', 'red', attrs=['reverse', 'blink']))

            try:
                cursor = connection.cursor()
                tableTrigger = table + tableVolumes
                cursor.execute(triggerInsert % (tableTrigger, tableTrigger))
                cursor.execute(triggerUpdate % (tableTrigger, tableTrigger))
                connection.commit()
                cursor.close()
            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na criação da trigger de volumes: {e.msg}', 'red')) 
                else:
                    print(colored(f'Erro na criação da trigger volume: {e.msg}', 'red', attrs=['reverse', 'blink']))

            try:
                cursor = connection.cursor()
                tableTrigger = table + tableChapters
                cursor.execute(triggerInsert % (tableTrigger, tableTrigger))
                cursor.execute(triggerUpdate % (tableTrigger, tableTrigger))
                connection.commit()
                cursor.close()
            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na criação da trigger de capítulos: {e.msg}', 'red')) 
                else:
                    print(colored(f'Erro na criação da trigger capitulo: {e.msg}', 'red', attrs=['reverse', 'blink']))

            try:
                cursor = connection.cursor()
                tableTrigger = table + tablePages
                cursor.execute(triggerInsert % (tableTrigger, tableTrigger))
                cursor.execute(triggerUpdate % (tableTrigger, tableTrigger))
                connection.commit()
                cursor.close()
            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na criação da trigger de páginas: {e.msg}', 'red')) 
                else:
                    print(colored(f'Erro na criação da trigger pagina: {e.msg}', 'red', attrs=['reverse', 'blink']))

            try:
                cursor = connection.cursor()
                tableTrigger = table + tableText
                cursor.execute(triggerInsert % (tableTrigger, tableTrigger))
                cursor.execute(triggerUpdate % (tableTrigger, tableTrigger))
                connection.commit()
                cursor.close()
            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na criação da trigger de texto: {e.msg}', 'red')) 
                else:
                    print(colored(f'Erro na criação da trigger texto: {e.msg}', 'red', attrs=['reverse', 'blink']))

            try:
                cursor = connection.cursor()
                tableTrigger = table + tableVocabulary
                cursor.execute(triggerUpdate % (tableTrigger, tableTrigger))
                connection.commit()
                cursor.close()
            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na criação da trigger de vocabulário: {e.msg}', 'red')) 
                else:
                    print(colored(f'Erro na criação da trigger vocabulario: {e.msg}', 'red', attrs=['reverse', 'blink']))

            try:
                cursor = connection.cursor()
                tableTrigger = table + tableCover
                cursor.execute(triggerInsert % (tableTrigger, tableTrigger))
                cursor.execute(triggerUpdate % (tableTrigger, tableTrigger))
                connection.commit()
                cursor.close()
            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na criação da trigger da capa: {e.msg}', 'red')) 
                else:
                    print(colored(f'Erro na criação da trigger vocabulario: {e.msg}', 'red', attrs=['reverse', 'blink']))


            self.table = table
            return table
        
    def convertToBinaryData(filename):
        # Convert digital data to binary format
        with open(filename, 'rb') as file:
            binaryData = file.read()
        return binaryData


    def deleteChapter(self, id_chapter=None):
        with conection() as connection:
            if (id_chapter is None):
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog('Erro ao excluir capítulo, não informado id.', 'red'))
                else:
                    print(colored('Erro ao excluir capítulo, não informado id.', 'red', attrs=['reverse', 'blink']))
                return
            
            if not self.operation.isTest:
                self.operation.window.write_event_value('-THREAD_LOG-', PrintLog('Apagando capítulos posteriores a partir do capítulo atual. ID: ' + str(id_chapter), 'yellow'))
            else:
                print(colored('Apagando capítulos posteriores a partir do capítulo atual. ID: ' + str(id_chapter), 'yellow', attrs=['reverse', 'blink']))

            try:
                cursor = connection.cursor(buffered=True)
                sql = selectNextChapters.format(self.operation.base, self.operation.base)
                cursor.execute(sql % str(id_chapter))
                connection.commit()

                if cursor.rowcount > 0:
                    for (row) in cursor:
                        try:
                            ID = row[0]
                            if not self.operation.isTest:
                                self.operation.window.write_event_value('-THREAD_LOG-', PrintLog('Apagando capítulo. ID: ' + ID, 'yellow'))
                            else:
                                print(colored('Apagando capítulo. ID: ' + ID, 'yellow', attrs=['reverse', 'blink']))

                            cursorDelete = connection.cursor()
                            connection.autocommit = False

                            sql = deleteVocabularyPageFromChapter.format(self.operation.base, self.operation.base, self.operation.base)
                            cursorDelete.execute(sql % ID)

                            sql = deleteVocabularyChapterFromChapter.format(self.operation.base, self.operation.base)
                            cursorDelete.execute(sql % ID)

                            sql = deleteTextsFromChapter.format(self.operation.base, self.operation.base, self.operation.base)
                            cursorDelete.execute(sql % ID)

                            sql = deletePagesFromChapter.format(self.operation.base, self.operation.base)
                            cursorDelete.execute(sql % ID)

                            sql = deleteChapter.format(self.operation.base)
                            cursorDelete.execute(sql % ID)

                            connection.commit()
                            cursorDelete.close()
                        except ProgrammingError as e:
                            connection.rollback()
                            if not self.operation.isTest:
                                self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao excluir capítulo: {e.msg}', 'red'))
                            else:
                                print(colored(f'Erro ao excluir capítulo: {e.msg}', 'red', attrs=['reverse', 'blink']))
                    
                    connection.autocommit = True

                cursor.close()
            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na exclusão a partir do capítulo: {e.msg}',  'red')) 
                else:
                    print(colored(f'Erro na exclusão a partir do capítulo: {e.msg}', 'red', attrs=['reverse', 'blink']))


    def saveCover(self, id_volume=None, volume=None):
        with conection() as connection:
            if (id_volume is None):
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog('Erro ao gravar a capa, não informado id.', 'red'))
                else:
                    print(colored('Erro ao gravar a capa, não informado id.', 'red', attrs=['reverse', 'blink']))
                return
            elif volume.cover is None:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog('Erro ao gravar a capa, capa não encontrada.', 'red'))
                else:
                    print(colored('Erro ao gravar a capa, capa não encontrada.', 'red', attrs=['reverse', 'blink']))
                return
            elif volume.cover.saved:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog('Capa já salva, retornando.', 'yellow'))
                else:
                    print(colored('Capa já salva, retornando.', 'yellow', attrs=['reverse', 'blink']))
                return
            elif not os.path.exists(volume.cover.file):
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog('Erro ao gravar a capa, arquivo de capa não encontrada.', 'red'))
                else:
                    print(colored('Erro ao gravar a capa, arquivo de capa não encontrada.', 'red', attrs=['reverse', 'blink']))
                return
            
            try:
                cover = volume.cover

                # Open a file in binary mode
                file = open(cover.file,'rb').read()
                
                # We must encode the file to get base64 string
                #file = base64.b64encode(file)

                cursor = connection.cursor(buffered=True)
                sql = selectCover.format(self.operation.base)
                cursor.execute(sql % str(id_volume))

                if cursor.rowcount > 0:
                    try:
                        args = (volume.name, volume.volume, volume.language, cover.fileName,
                                cover.extension, file, cursor.fetchone()[0])
                        sql = updateCover.format(self.operation.base)
                        cursor.execute(sql, args)
                        connection.commit()
                        cover.saved = True
                    except ProgrammingError as e:
                        if not self.operation.isTest:
                            self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao atualizar os dados: {e.msg}', 'red'))
                        else:
                            print(colored(f'Erro ao atualizar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))
                else:
                    try:
                        id = uuid.uuid4()
                        args = (str(id), str(id_volume), volume.name, volume.volume, volume.language,
                                cover.fileName, cover.extension, file)
                        
                        sql = insertCover.format(self.operation.base)
                        cursor.execute(sql, args)
                        connection.commit()
                        cover.saved = True
                    except ProgrammingError as e:
                        if not self.operation.isTest:
                            self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao gravar os dados: {e.msg}', 'red'))
                        else:
                            print(colored(f'Erro ao gravar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))

                cursor.close()
            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao consultar registro: {e.msg}',  'red'))
                else:
                    print(colored(f'Erro ao consultar registro: {e.msg}', 'red', attrs=['reverse', 'blink']))


    def saveText(self, id_page=None, text=None):
        with conection() as connection:
            if (id_page is None) or (text is None):
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog('Erro ao gravar os dados, não informado id.', 'red'))
                else:
                    print(colored('Erro ao gravar os dados, não informado id.', 'red', attrs=['reverse', 'blink']))
                return
            elif text is None:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog('Erro ao gravar os dados, dados para inserção vazio.', 'red'))
                else:
                    print(colored('Erro ao gravar os dados, dados para inserção vazio.', 'red', attrs=['reverse', 'blink']))
                return
            try:
                args = (str(id_page), text.text)
                cursor = connection.cursor(buffered=True)
                sql = selectText.format(self.operation.base)
                cursor.execute(sql, args)

                if cursor.rowcount > 0:
                    try:
                        args = (text.sequence, text.text, text.posX1, text.posY1,
                                text.posX2, text.posY2, APPLICATION_VERSION, cursor.fetchone()[0])
                        sql = updateText.format(self.operation.base)
                        cursor.execute(sql, args)
                        connection.commit()
                    except ProgrammingError as e:
                        if not self.operation.isTest:
                            self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao atualizar os dados: {e.msg}', 'red'))
                        else:
                            print(colored(f'Erro ao atualizar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))
                else:
                    try:
                        id = uuid.uuid4()
                        args = (str(id), str(id_page), text.sequence, text.text, text.posX1,
                                text.posY1, text.posX2, text.posY2, APPLICATION_VERSION)
                        sql = insertText.format(self.operation.base)
                        cursor.execute(sql, args)
                        connection.commit()
                    except ProgrammingError as e:
                        if not self.operation.isTest:
                            self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao gravar os dados: {e.msg}', 'red'))
                        else:
                            print(colored(f'Erro ao gravar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))

                cursor.close()
            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao consultar registro: {e.msg}',  'red'))
                else:
                    print(colored(f'Erro ao consultar registro: {e.msg}', 'red', attrs=['reverse', 'blink']))


    def savePage(self, id_chapter=None, page=None):
        with conection() as connection:
            if (id_chapter is None) or (page is None):
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog('Erro ao gravar os dados, dados para inserção vazio.', 'red')) 
                else:
                    print(colored('Erro ao gravar os dados, dados para inserção vazio.', 'red', attrs=['reverse', 'blink']))
                return

            try:
                id = None
                args = (str(id_chapter), page.name, page.hashPage)
                cursor = connection.cursor(buffered=True)
                sql = selectPage.format(self.operation.base)
                cursor.execute(sql, args)

                if cursor.rowcount > 0:
                    try:
                        id = uuid.UUID(cursor.fetchone()[0])
                        args = (page.name, page.number, page.hashPage, str(id))
                        sql = updatePage.format(self.operation.base)
                        cursor.execute(sql, args)
                        connection.commit()
                    except ProgrammingError as e:
                        if not self.operation.isTest:
                            self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao atualizar os dados: {e.msg}', 'red')) 
                        else:
                            print(colored(f'Erro ao atualizar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))
                else:
                    try:
                        id = uuid.uuid4()
                        args = (str(id), str(id_chapter), page.name, page.number, page.hashPage)
                        sql = insertPage.format(self.operation.base)
                        cursor.execute(sql, args)
                        connection.commit()
                    except ProgrammingError as e:
                        if not self.operation.isTest:
                            self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao gravar os dados: {e.msg}', 'red')) 
                        else:
                            print(colored(f'Erro ao gravar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))

                cursor.close()
                for text in page.texts:
                    self.saveText(id, text)

            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao consultar registro: {e.msg}',  'red')) 
                else:
                    print(colored(f'Erro ao consultar registro: {e.msg}', 'red', attrs=['reverse', 'blink']))


    def saveChapter(self, id_volume=None, chapter=None):
        with conection() as connection:
            if (id_volume is None) or (chapter is None):
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog('Erro ao gravar os dados, dados para inserção vazio.', 'red')) 
                else:
                    print(colored('Erro ao gravar os dados, dados para inserção vazio.', 'red', attrs=['reverse', 'blink']))
                return

            try:
                id = None
                args = (str(id_volume), chapter.name, chapter.volume, chapter.chapter, chapter.language, chapter.isExtra)
                cursor = connection.cursor(buffered=True)
                sql = selectChapter.format(self.operation.base)
                cursor.execute(sql, args)

                if (cursor.rowcount > 0) and (not chapter.isExtra):
                    id = uuid.UUID(cursor.fetchone()[0])
                    self.deleteChapter(id)
                    connection.commit() # Clear buffer
                    cursor.execute(sql, args)
                    
                if cursor.rowcount > 0:
                    try:
                        id = uuid.UUID(cursor.fetchone()[0])
                        args = (chapter.name, chapter.volume, chapter.chapter, chapter.language, 
                                chapter.scan, chapter.isExtra, chapter.isScan, str(id))
                        sql = updateChapter.format(self.operation.base)
                        cursor.execute(sql, args)
                        connection.commit()
                    except ProgrammingError as e:
                        if not self.operation.isTest:
                            self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao atualizar os dados: {e.msg}', 'red')) 
                        else:
                            print(colored(f'Erro ao atualizar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))
                else:
                    try:
                        id = uuid.uuid4()
                        args = (str(id), str(id_volume), chapter.name, chapter.volume, chapter.chapter,
                                chapter.language, chapter.scan, chapter.isExtra, chapter.isScan)
                        sql = insertChapter.format(self.operation.base)
                        cursor.execute(sql, args)
                        connection.commit()
                    except ProgrammingError as e:
                        if not self.operation.isTest:
                            self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao gravar os dados: {e.msg}', 'red')) 
                        else:
                            print(colored(f'Erro ao gravar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))

                cursor.close()
                for page in chapter.pages:
                    self.savePage(id, page)

            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao consultar registro: {e.msg}',  'red')) 
                else:
                    print(colored(f'Erro ao consultar registro: {e.msg}', 'red', attrs=['reverse', 'blink']))


    def saveVolume(self, volume=None):
        with conection() as connection:
            if (volume is None):
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog('Erro ao gravar os dados, dados para inserção vazio.', 'red')) 
                else:
                    print(colored('Erro ao gravar os dados, dados para inserção vazio.', 'red', attrs=['reverse', 'blink']))
                return None

            try:
                id = None
                args = (volume.name, volume.volume, volume.language)
                cursor = connection.cursor(buffered=True)
                sql = selectVolume.format(self.operation.base)
                cursor.execute(sql, args)

                if cursor.rowcount > 0:
                    try:
                        id = uuid.UUID(cursor.fetchone()[0])
                        args = (volume.name, volume.volume, volume.language, str(id))
                        sql = updateVolume.format(self.operation.base)
                        cursor.execute(sql, args)
                        connection.commit()
                    except ProgrammingError as e:
                        if not self.operation.isTest:
                            self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao atualizar os dados: {e.msg}', 'red')) 
                        else:
                            print(colored(f'Erro ao atualizar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))
                else:
                    try:
                        id = uuid.uuid4()
                        args = (str(id), volume.name, volume.volume, volume.language)
                        sql = insertVolume.format(self.operation.base)
                        cursor.execute(sql, args)
                        connection.commit()
                    except ProgrammingError as e:
                        if not self.operation.isTest:
                            self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao gravar os dados: {e.msg}', 'red')) 
                        else:
                            print(colored(f'Erro ao gravar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))

                cursor.close()
                for chapter in volume.chapters:
                    self.saveChapter(id, chapter)

                self.saveCover(id, volume)
                
            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao consultar registro: {e.msg}',  'red')) 
                else:
                    print(colored(f'Erro ao consultar registro: {e.msg}', 'red', attrs=['reverse', 'blink']))


class TableLocate:
    def __init__(self, exists):
        self.exists = exists
        self.table = ''
        self.lastVolume = ''
        self.obs = ''


def testConnection():
    with conection() as connection:
        return connection.is_connected()


def findTable(tableName, mangaName, language):
    util = BdUtil(None)
    table = tableName.replace(" ", "_")
    locate = TableLocate(util.existTable(table))

    if locate.exists:
        locate.lastVolume = util.lastVolume(table, mangaName, language)
    else:
        locate.lastVolume = 'Tabela será criada.'

    return locate
    

def saveData(operation, chapter, cover):
    if operation.base is None:
        raise ValueError("Erro ao gravar os dados, table não informada.")

    util = BdUtil(operation)

    log = "Manga: " + chapter.name + " - Volume: " + chapter.volume + " - Chapter: " + chapter.chapter
    if not operation.isTest:
        operation.window.write_event_value('-THREAD_LOG-', PrintLog('Gravando informações no banco de dados....', 'blue'))
        operation.window.write_event_value('-THREAD_LOG-', PrintLog(log)) 
    elif operation.isSilent:
        printLog(PrintLog('Gravando informações no banco de dados....', directory=operation.applicationPath, isSilent=operation.isSilent))
    else:
        print(colored('Gravando informações no banco de dados....', 'blue', attrs=['reverse', 'blink']))
        print(log)

    util.saveVolume(Volume(chapter.name, chapter.volume, chapter.language, chapter, cover))

    if not operation.isTest:
        operation.window.write_event_value('-THREAD_LOG-', PrintLog('Gravação concluida.', 'blue'))
    elif operation.isSilent:
        printLog(PrintLog('Gravação concluida', directory=operation.applicationPath, isSilent=operation.isSilent))
    else:
        print(colored('Gravação concluida.', 'blue', attrs=['reverse', 'blink']))
