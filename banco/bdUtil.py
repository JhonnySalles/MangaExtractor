from PySimpleGUI.PySimpleGUI import No
from mysql.connector.errors import ProgrammingError
from .bd import conection
from termcolor import colored
import sys
sys.path.append("../")
from classes import PrintLog, Volume
from util import printLog
from defaults import BD_NAME, APPLICATION_VERSION

volumes = """
    CREATE TABLE %s_volumes (
    id int(11) NOT NULL AUTO_INCREMENT,
    manga varchar(250) DEFAULT NULL,
    volume int(4) DEFAULT NULL,
    linguagem varchar(6) DEFAULT NULL,
    arquivo varchar(250) DEFAULT NULL,
    is_processado Tinyint(1) DEFAULT '0',
    PRIMARY KEY (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
"""
chapters = """
    CREATE TABLE IF NOT EXISTS %s_capitulos (
        id INT NOT NULL AUTO_INCREMENT,
        id_volume INT(11) DEFAULT NULL,
        manga LONGTEXT NOT NULL,
        volume INT(4) NOT NULL,
        capitulo DOUBLE NOT NULL,
        linguagem VARCHAR(6),
        scan VARCHAR(250),
        is_extra Tinyint(1) DEFAULT '0',
        is_raw BOOLEAN,
        is_processado Tinyint(1) DEFAULT '0',
        PRIMARY KEY (id),
        KEY %s_volumes_fk (id_volume),
        CONSTRAINT %s_volumes_capitulos_fk FOREIGN KEY (id_volume) REFERENCES %s_volumes (id) ON DELETE CASCADE ON UPDATE CASCADE
    ) CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; 
"""
pages = """
    CREATE TABLE IF NOT EXISTS %s_paginas (
        id INT NOT NULL AUTO_INCREMENT,
        id_capitulo int(11) NOT NULL,
        nome VARCHAR(250) DEFAULT NULL,
        numero INT(11),
        hash_pagina VARCHAR(250),
        is_processado Tinyint(1) DEFAULT '0',
        PRIMARY KEY (id),
        KEY %s_capitulos_fk (id_capitulo),
        CONSTRAINT %s_capitulos_paginas_fk FOREIGN KEY (id_capitulo) REFERENCES %s_capitulos (id) ON DELETE CASCADE ON UPDATE CASCADE
    ) CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""
text = """
    CREATE TABLE IF NOT EXISTS %s_textos (
        id INT NOT NULL AUTO_INCREMENT,
        id_pagina INT(11) NOT NULL,
        sequencia INT(4),
        texto LONGTEXT NOT NULL,
        posicao_x1 DOUBLE DEFAULT NULL,
        posicao_y1 DOUBLE DEFAULT NULL,
        posicao_x2 DOUBLE DEFAULT NULL,
        posicao_y2 DOUBLE DEFAULT NULL,
        versaoApp int(11) DEFAULT '0', 
        PRIMARY KEY (id),
        KEY %s_paginas_fk (id_pagina),
        CONSTRAINT %s_paginas_textos_fk FOREIGN KEY (id_pagina) REFERENCES %s_paginas (id) ON DELETE CASCADE ON UPDATE CASCADE
    ) CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

selectVolume = 'SELECT id FROM {}_volumes WHERE manga = %s AND volume = %s AND linguagem = %s '
insertVolume = """
    INSERT INTO {}_volumes (manga, volume, linguagem) 
    VALUES (%s, %s, %s)
"""
updateVolume = """
    UPDATE {}_volumes SET manga = %s, volume = %s, linguagem = %s
    WHERE id = %s
"""

selectChapter = 'SELECT id FROM {}_capitulos WHERE id_volume = %s AND manga = %s AND volume = %s AND capitulo = %s AND linguagem = %s AND is_extra = %s '
insertChapter = """
    INSERT INTO {}_capitulos (id_volume, manga, volume, capitulo, linguagem, scan, is_extra, is_raw) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""
updateChapter = """
    UPDATE {}_capitulos SET manga = %s, volume = %s, capitulo = %s, linguagem = %s, scan = %s, is_extra = %s, is_raw = %s, is_processado = 0
    WHERE id = %s
"""

selectPage = 'SELECT id FROM {}_paginas WHERE id_capitulo = %s AND nome = %s AND hash_pagina = %s '
insertPage = """
    INSERT INTO {}_paginas (id_capitulo, nome, numero, hash_pagina) 
    VALUES (%s, %s, %s, %s)
"""
updatePage = """
    UPDATE {}_paginas SET nome = %s, numero = %s, hash_pagina = %s, is_processado = 0
    WHERE id = %s
"""

selectText = 'SELECT id FROM {}_textos WHERE id_pagina = %s AND texto = %s '
insertText = """
    INSERT INTO {}_textos (id_pagina, sequencia, texto, posicao_x1, posicao_y1, posicao_x2, posicao_y2, versaoApp) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""
updateText = """
    UPDATE {}_textos SET sequencia = %s, texto = %s, posicao_x1 = %s, posicao_y1 = %s, posicao_x2 = %s, posicao_y2 = %s, versaoApp = %s
    WHERE id = %s
"""

tableExists = """
    SELECT Table_Name FROM information_schema.tables 
    WHERE table_schema = "%s" 
    AND (Table_Name LIKE "%s_textos")
    GROUP BY Table_Name
"""


class BdUtil:
    def __init__(self, operation):
        self.operation = operation
        self.table = ''


    def createTable(self, name=None):
        with conection() as connection:
            if name == None:
                raise ValueError("Erro na criação da table, table não informada.")

            table = name.replace(" ", "_")
            try:
                cursor = connection.cursor(buffered=True)
                cursor.execute(tableExists % (BD_NAME, table))

                if cursor.rowcount > 0:
                    if not self.operation.isTest:
                        self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Estrutura de tabelas já existente. Tabela: {table}', 'red')) 
                    else:
                        print(colored(f'Estrutura de tabelas já existente. Tabela: {table}', 'red', attrs=['reverse', 'blink']))
                    self.table = table
                    return table
            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na criação da table volume: {e.msg}', 'red')) 
                else:
                    print(colored(f'Erro na criação da table volume: {e.msg}', 'red', attrs=['reverse', 'blink']))

            try:
                cursor = connection.cursor()
                cursor.execute(volumes % table)
                connection.commit()
            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na criação da table volume: {e.msg}', 'red')) 
                else:
                    print(colored(f'Erro na criação da table volume: {e.msg}', 'red', attrs=['reverse', 'blink']))

            try:
                cursor = connection.cursor()
                cursor.execute(chapters % (table, table, table, table))
                connection.commit()
            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na criação da table chapter: {e.msg}', 'red')) 
                else:
                    print(colored(f'Erro na criação da table chapter: {e.msg}', 'red', attrs=['reverse', 'blink']))

            try:
                cursor = connection.cursor()
                cursor.execute(pages % (table, table, table, table))
                connection.commit()
            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na criação da table page: {e.msg}', 'red')) 
                else:
                    print(colored(f'Erro na criação da table page: {e.msg}', 'red', attrs=['reverse', 'blink']))

            try:
                cursor = connection.cursor()
                cursor.execute(text % (table, table, table, table))
                connection.commit()
            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na criação da table text: {e.msg}', 'red'))
                else:
                    print(colored(f'Erro na criação da table text: {e.msg}', 'red', attrs=['reverse', 'blink']))

            self.table = table
            return table


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
                args = (id_page, text.text)
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
                        args = (id_page, text.sequence, text.text, text.posX1,
                                text.posY1, text.posX2, text.posY2, APPLICATION_VERSION)
                        sql = insertText.format(self.operation.base)
                        cursor.execute(sql, args)
                        connection.commit()
                    except ProgrammingError as e:
                        if not self.operation.isTest:
                            self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao gravar os dados: {e.msg}', 'red'))
                        else:
                            print(colored(f'Erro ao gravar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))
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
                args = (id_chapter, page.name, page.hashPage)
                cursor = connection.cursor(buffered=True)
                sql = selectPage.format(self.operation.base)
                cursor.execute(sql, args)

                if cursor.rowcount > 0:
                    try:
                        id = cursor.fetchone()[0]
                        args = (page.name, page.number, page.hashPage, id)
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
                        args = (id_chapter, page.name, page.number, page.hashPage)
                        sql = insertPage.format(self.operation.base)
                        cursor.execute(sql, args)
                        connection.commit()
                        id = cursor.lastrowid
                    except ProgrammingError as e:
                        if not self.operation.isTest:
                            self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao gravar os dados: {e.msg}', 'red')) 
                        else:
                            print(colored(f'Erro ao gravar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))

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
                args = (id_volume, chapter.name, chapter.volume, chapter.chapter, chapter.language, chapter.isExtra)
                cursor = connection.cursor(buffered=True)
                sql = selectChapter.format(self.operation.base)
                cursor.execute(sql, args)

                if cursor.rowcount > 0:
                    try:
                        id = cursor.fetchone()[0]
                        args = (chapter.name, chapter.volume, chapter.chapter, chapter.language, 
                                chapter.scan, chapter.isExtra, chapter.isScan, id)
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
                        args = (id_volume, chapter.name, chapter.volume, chapter.chapter,
                                chapter.language, chapter.scan, chapter.isExtra, chapter.isScan)
                        sql = insertChapter.format(self.operation.base)
                        cursor.execute(sql, args)
                        connection.commit()
                        id = cursor.lastrowid
                    except ProgrammingError as e:
                        if not self.operation.isTest:
                            self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao gravar os dados: {e.msg}', 'red')) 
                        else:
                            print(colored(f'Erro ao gravar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))

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
                        id = cursor.fetchone()[0]
                        args = (volume.name, volume.volume, volume.language, id)
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
                        args = (volume.name, volume.volume, volume.language)
                        sql = insertVolume.format(self.operation.base)
                        cursor.execute(sql, args)
                        connection.commit()
                        id = cursor.lastrowid
                    except ProgrammingError as e:
                        if not self.operation.isTest:
                            self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao gravar os dados: {e.msg}', 'red')) 
                        else:
                            print(colored(f'Erro ao gravar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))

                for chapter in volume.chapters:
                        self.saveChapter(id, chapter)

            except ProgrammingError as e:
                if not self.operation.isTest:
                    self.operation.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao consultar registro: {e.msg}',  'red')) 
                else:
                    print(colored(f'Erro ao consultar registro: {e.msg}', 'red', attrs=['reverse', 'blink']))


def testConnection():
    with conection() as connection:
        return connection.is_connected()


def saveData(operation, chapter):
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

    util.saveVolume(Volume(chapter.name, chapter.volume, chapter.language, chapter))

    if not operation.isTest:
        operation.window.write_event_value('-THREAD_LOG-', PrintLog('Gravação concluida.', 'blue'))
    elif operation.isSilent:
        printLog(PrintLog('Gravação concluida', directory=operation.applicationPath, isSilent=operation.isSilent))
    else:
        print(colored('Gravação concluida.', 'blue', attrs=['reverse', 'blink']))
