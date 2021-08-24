from PySimpleGUI.PySimpleGUI import No
from mysql.connector.errors import ProgrammingError
from .bd import conection
from termcolor import colored
import sys
sys.path.append("../")
from classes import PrintLog, Volume
from util import printLog
from defaults import NOME_DB

volumes = """
    CREATE TABLE %s_volumes (
    id int(11) NOT NULL AUTO_INCREMENT,
    manga varchar(250) DEFAULT NULL,
    volume int(4) DEFAULT NULL,
    linguagem varchar(4) DEFAULT NULL,
    vocabulario longtext,
    PRIMARY KEY (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
"""
capitulos = """
    CREATE TABLE IF NOT EXISTS %s_capitulos (
        id INT NOT NULL AUTO_INCREMENT,
        id_volume INT(11) DEFAULT NULL,
        manga LONGTEXT NOT NULL,
        volume INT(4) NOT NULL,
        capitulo DOUBLE NOT NULL,
        linguagem VARCHAR(4),
        scan VARCHAR(250),
        is_extra Tinyint(1) DEFAULT '0',
        is_raw BOOLEAN,
        is_processado Tinyint(1) DEFAULT '0',
        vocabulario LONGTEXT COLLATE utf8mb4_unicode_ci,
        PRIMARY KEY (id),
        KEY %s_volumes_capitulos_fk (id_volume),
        CONSTRAINT %s_volumes_capitulos_fk FOREIGN KEY (id_volume) REFERENCES %s_volumes (id) ON DELETE CASCADE ON UPDATE CASCADE
    ) CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; 
"""
paginas = """
    CREATE TABLE IF NOT EXISTS %s_paginas (
        id INT NOT NULL AUTO_INCREMENT,
        id_capitulo int(11) NOT NULL,
        nome VARCHAR(250) DEFAULT NULL,
        numero INT(11),
        hash_pagina VARCHAR(250),
        is_processado Tinyint(1) DEFAULT '0',
        vocabulario LONGTEXT,
        PRIMARY KEY (id),
        KEY %s_capitulos_paginas_fk (id_capitulo),
        CONSTRAINT %s_capitulos_paginas_fk FOREIGN KEY (id_capitulo) REFERENCES %s_capitulos (id) ON DELETE CASCADE ON UPDATE CASCADE
    ) CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""
textos = """
    CREATE TABLE IF NOT EXISTS %s_textos (
        id INT NOT NULL AUTO_INCREMENT,
        id_pagina INT(11) NOT NULL,
        sequencia INT(4),
        texto LONGTEXT NOT NULL,
        posicao_x1 DOUBLE DEFAULT NULL,
        posicao_y1 DOUBLE DEFAULT NULL,
        posicao_x2 DOUBLE DEFAULT NULL,
        posicao_y2 DOUBLE DEFAULT NULL, PRIMARY KEY (id),
        KEY %s_paginas_textos_fk (id_pagina),
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

selectCapitulo = 'SELECT id FROM {}_capitulos WHERE id_volume = %s AND manga = %s AND volume = %s AND capitulo = %s AND linguagem = %s AND is_extra = %s '
insertCapitulo = """
    INSERT INTO {}_capitulos (id_volume, manga, volume, capitulo, linguagem, scan, is_extra, is_raw) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""
updateCapitulo = """
    UPDATE {}_capitulos SET manga = %s, volume = %s, capitulo = %s, linguagem = %s, scan = %s, is_extra = %s, is_raw = %s, is_processado = 0
    WHERE id = %s
"""

selectPagina = 'SELECT id FROM {}_paginas WHERE id_capitulo = %s AND nome = %s AND hash_pagina = %s '
insertPagina = """
    INSERT INTO {}_paginas (id_capitulo, nome, numero, hash_pagina) 
    VALUES (%s, %s, %s, %s)
"""
updatePagina = """
    UPDATE {}_paginas SET nome = %s, numero = %s, hash_pagina = %s, is_processado = 0
    WHERE id = %s
"""

selectTexto = 'SELECT id FROM {}_textos WHERE id_pagina = %s AND texto = %s '
insertTexto = """
    INSERT INTO {}_textos (id_pagina, sequencia, texto, posicao_x1, posicao_y1, posicao_x2, posicao_y2) 
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""
updateTexto = """
    UPDATE {}_textos SET sequencia = %s, texto = %s, posicao_x1 = %s, posicao_y1 = %s, posicao_x2 = %s, posicao_y2 = %s
    WHERE id = %s
"""

tabelaExist = """
    SELECT Table_Name FROM information_schema.tables 
    WHERE table_schema = "%s" 
    AND (Table_Name LIKE "%s_textos")
    GROUP BY Table_Name
"""


class BdUtil:
    def __init__(self, operacao):
        self.operacao = operacao
        self.tabela = ''


    def criaTabela(self, nome=None):
        with conection() as conexao:
            if nome == None:
                raise ValueError("Erro na criação da tabela, tabela não informada.")

            tabela = nome.replace(" ", "_")
            try:
                cursor = conexao.cursor(buffered=True)
                cursor.execute(tabelaExist % (NOME_DB, tabela))

                if cursor.rowcount > 0:
                    if not self.operacao.isTeste:
                        self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(f'Estrutura de tabelas já existente. Tabela: {tabela}', 'red')) 
                    else:
                        print(colored(f'Estrutura de tabelas já existente. Tabela: {tabela}', 'red', attrs=['reverse', 'blink']))
                    self.tabela = tabela
                    return tabela
            except ProgrammingError as e:
                if not self.operacao.isTeste:
                    self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na criação da tabela volume: {e.msg}', 'red')) 
                else:
                    print(colored(f'Erro na criação da tabela volume: {e.msg}', 'red', attrs=['reverse', 'blink']))

            try:
                cursor = conexao.cursor()
                cursor.execute(volumes % tabela)
                conexao.commit()
            except ProgrammingError as e:
                if not self.operacao.isTeste:
                    self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na criação da tabela volume: {e.msg}', 'red')) 
                else:
                    print(colored(f'Erro na criação da tabela volume: {e.msg}', 'red', attrs=['reverse', 'blink']))

            try:
                cursor = conexao.cursor()
                cursor.execute(capitulos % (tabela, tabela, tabela, tabela))
                conexao.commit()
            except ProgrammingError as e:
                if not self.operacao.isTeste:
                    self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na criação da tabela capitulo: {e.msg}', 'red')) 
                else:
                    print(colored(f'Erro na criação da tabela capitulo: {e.msg}', 'red', attrs=['reverse', 'blink']))

            try:
                cursor = conexao.cursor()
                cursor.execute(paginas % (tabela, tabela, tabela, tabela))
                conexao.commit()
            except ProgrammingError as e:
                if not self.operacao.isTeste:
                    self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na criação da tabela pagina: {e.msg}', 'red')) 
                else:
                    print(colored(f'Erro na criação da tabela pagina: {e.msg}', 'red', attrs=['reverse', 'blink']))

            try:
                cursor = conexao.cursor()
                cursor.execute(textos % (tabela, tabela, tabela, tabela))
                conexao.commit()
            except ProgrammingError as e:
                if not self.operacao.isTeste:
                    self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro na criação da tabela texto: {e.msg}', 'red'))
                else:
                    print(colored(f'Erro na criação da tabela texto: {e.msg}', 'red', attrs=['reverse', 'blink']))

            self.tabela = tabela
            return tabela


    def gravaTexto(self, id_pagina=None, texto=None):
        with conection() as conexao:
            if (id_pagina is None) or (texto is None):
                if not self.operacao.isTeste:
                    self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog('Erro ao gravar os dados, não informado id.', 'red'))
                else:
                    print(colored('Erro ao gravar os dados, não informado id.', 'red', attrs=['reverse', 'blink']))
                return
            elif texto is None:
                if not self.operacao.isTeste:
                    self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog('Erro ao gravar os dados, dados para inserção vazio.', 'red'))
                else:
                    print(colored('Erro ao gravar os dados, dados para inserção vazio.', 'red', attrs=['reverse', 'blink']))
                return
            try:
                args = (id_pagina, texto.texto)
                cursor = conexao.cursor(buffered=True)
                sql = selectTexto.format(self.operacao.base)
                cursor.execute(sql, args)

                if cursor.rowcount > 0:
                    try:
                        args = (texto.sequencia, texto.texto, texto.posX1, texto.posY1,
                                texto.posX2, texto.posY2, cursor.fetchone()[0])
                        sql = updateTexto.format(self.operacao.base)
                        cursor.execute(sql, args)
                        conexao.commit()
                    except ProgrammingError as e:
                        if not self.operacao.isTeste:
                            self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao atualizar os dados: {e.msg}', 'red'))
                        else:
                            print(colored(f'Erro ao atualizar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))
                else:
                    try:
                        args = (id_pagina, texto.sequencia, texto.texto, texto.posX1,
                                texto.posY1, texto.posX2, texto.posY2)
                        sql = insertTexto.format(self.operacao.base)
                        cursor.execute(sql, args)
                        conexao.commit()
                    except ProgrammingError as e:
                        if not self.operacao.isTeste:
                            self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao gravar os dados: {e.msg}', 'red'))
                        else:
                            print(colored(f'Erro ao gravar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))
            except ProgrammingError as e:
                if not self.operacao.isTeste:
                    self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao consultar registro: {e.msg}',  'red'))
                else:
                    print(colored(f'Erro ao consultar registro: {e.msg}', 'red', attrs=['reverse', 'blink']))


    def gravaPagina(self, id_capitulo=None, pagina=None):
        with conection() as conexao:
            if (id_capitulo is None) or (pagina is None):
                if not self.operacao.isTeste:
                    self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog('Erro ao gravar os dados, dados para inserção vazio.', 'red')) 
                else:
                    print(colored('Erro ao gravar os dados, dados para inserção vazio.', 'red', attrs=['reverse', 'blink']))
                return

            try:
                id = None
                args = (id_capitulo, pagina.nome, pagina.hashPagina)
                cursor = conexao.cursor(buffered=True)
                sql = selectPagina.format(self.operacao.base)
                cursor.execute(sql, args)

                if cursor.rowcount > 0:
                    try:
                        id = cursor.fetchone()[0]
                        args = (pagina.nome, pagina.numero, pagina.hashPagina, id)
                        sql = updatePagina.format(self.operacao.base)
                        cursor.execute(sql, args)
                        conexao.commit()
                    except ProgrammingError as e:
                        if not self.operacao.isTeste:
                            self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao atualizar os dados: {e.msg}', 'red')) 
                        else:
                            print(colored(f'Erro ao atualizar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))
                else:
                    try:
                        args = (id_capitulo, pagina.nome, pagina.numero, pagina.hashPagina)
                        sql = insertPagina.format(self.operacao.base)
                        cursor.execute(sql, args)
                        conexao.commit()
                        id = cursor.lastrowid
                    except ProgrammingError as e:
                        if not self.operacao.isTeste:
                            self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao gravar os dados: {e.msg}', 'red')) 
                        else:
                            print(colored(f'Erro ao gravar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))

                for texto in pagina.textos:
                    self.gravaTexto(id, texto)

            except ProgrammingError as e:
                if not self.operacao.isTeste:
                    self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao consultar registro: {e.msg}',  'red')) 
                else:
                    print(colored(f'Erro ao consultar registro: {e.msg}', 'red', attrs=['reverse', 'blink']))


    def gravaCapitulo(self, id_volume=None, capitulo=None):
        with conection() as conexao:
            if (id_volume is None) or (capitulo is None):
                if not self.operacao.isTeste:
                    self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog('Erro ao gravar os dados, dados para inserção vazio.', 'red')) 
                else:
                    print(colored('Erro ao gravar os dados, dados para inserção vazio.', 'red', attrs=['reverse', 'blink']))
                return

            try:
                id = None
                args = (id_volume, capitulo.nome, capitulo.volume, capitulo.capitulo, capitulo.linguagem, capitulo.isExtra)
                cursor = conexao.cursor(buffered=True)
                sql = selectCapitulo.format(self.operacao.base)
                cursor.execute(sql, args)

                if cursor.rowcount > 0:
                    try:
                        id = cursor.fetchone()[0]
                        args = (capitulo.nome, capitulo.volume, capitulo.capitulo, capitulo.linguagem, 
                                capitulo.scan, capitulo.isExtra, capitulo.isScan, id)
                        sql = updateCapitulo.format(self.operacao.base)
                        cursor.execute(sql, args)
                        conexao.commit()
                    except ProgrammingError as e:
                        if not self.operacao.isTeste:
                            self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao atualizar os dados: {e.msg}', 'red')) 
                        else:
                            print(colored(f'Erro ao atualizar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))
                else:
                    try:
                        args = (id_volume, capitulo.nome, capitulo.volume, capitulo.capitulo,
                                capitulo.linguagem, capitulo.scan, capitulo.isExtra, capitulo.isScan)
                        sql = insertCapitulo.format(self.operacao.base)
                        cursor.execute(sql, args)
                        conexao.commit()
                        id = cursor.lastrowid
                    except ProgrammingError as e:
                        if not self.operacao.isTeste:
                            self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao gravar os dados: {e.msg}', 'red')) 
                        else:
                            print(colored(f'Erro ao gravar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))

                for pagina in capitulo.paginas:
                    self.gravaPagina(id, pagina)

            except ProgrammingError as e:
                if not self.operacao.isTeste:
                    self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao consultar registro: {e.msg}',  'red')) 
                else:
                    print(colored(f'Erro ao consultar registro: {e.msg}', 'red', attrs=['reverse', 'blink']))


    def gravaVolume(self, volume=None):
        with conection() as conexao:
            if (volume is None):
                if not self.operacao.isTeste:
                    self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog('Erro ao gravar os dados, dados para inserção vazio.', 'red')) 
                else:
                    print(colored('Erro ao gravar os dados, dados para inserção vazio.', 'red', attrs=['reverse', 'blink']))
                return None

            try:
                id = None
                args = (volume.nome, volume.volume, volume.linguagem)
                cursor = conexao.cursor(buffered=True)
                sql = selectVolume.format(self.operacao.base)
                cursor.execute(sql, args)

                if cursor.rowcount > 0:
                    try:
                        id = cursor.fetchone()[0]
                        args = (volume.nome, volume.volume, volume.linguagem, id)
                        sql = updateVolume.format(self.operacao.base)
                        cursor.execute(sql, args)
                        conexao.commit()
                    except ProgrammingError as e:
                        if not self.operacao.isTeste:
                            self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao atualizar os dados: {e.msg}', 'red')) 
                        else:
                            print(colored(f'Erro ao atualizar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))
                else:
                    try:
                        args = (volume.nome, volume.volume, volume.linguagem)
                        sql = insertVolume.format(self.operacao.base)
                        cursor.execute(sql, args)
                        conexao.commit()
                        id = cursor.lastrowid
                    except ProgrammingError as e:
                        if not self.operacao.isTeste:
                            self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao gravar os dados: {e.msg}', 'red')) 
                        else:
                            print(colored(f'Erro ao gravar os dados: {e.msg}', 'red', attrs=['reverse', 'blink']))

                for capitulo in volume.capitulos:
                        self.gravaCapitulo(id, capitulo)

            except ProgrammingError as e:
                if not self.operacao.isTeste:
                    self.operacao.window.write_event_value('-THREAD_LOG-', PrintLog(f'Erro ao consultar registro: {e.msg}',  'red')) 
                else:
                    print(colored(f'Erro ao consultar registro: {e.msg}', 'red', attrs=['reverse', 'blink']))


def testaConexao():
    with conection() as conexao:
        return conexao.is_connected()


def gravarDados(operacao, capitulo):
    if operacao.base is None:
        raise ValueError("Erro ao gravar os dados, tabela não informada.")

    util = BdUtil(operacao)

    log = "Manga: " + capitulo.nome + " - Volume: " + capitulo.volume + " - Capitulo: " + capitulo.capitulo
    if not operacao.isTeste:
        operacao.window.write_event_value('-THREAD_LOG-', PrintLog('Gravando informações no banco de dados....', 'blue'))
        operacao.window.write_event_value('-THREAD_LOG-', PrintLog(log)) 
    elif operacao.isSilent:
        printLog(PrintLog('Gravando informações no banco de dados....', caminho=operacao.caminhoAplicacao, isSilent=operacao.isSilent))
    else:
        print(colored('Gravando informações no banco de dados....', 'blue', attrs=['reverse', 'blink']))
        print(log)

    util.gravaVolume(Volume(capitulo.nome, capitulo.volume, capitulo.linguagem, capitulo))

    if not operacao.isTeste:
        operacao.window.write_event_value('-THREAD_LOG-', PrintLog('Gravação concluida.', 'blue'))
    elif operacao.isSilent:
        printLog(PrintLog('Gravação concluida', caminho=operacao.caminhoAplicacao, isSilent=operacao.isSilent))
    else:
        print(colored('Gravação concluida.', 'blue', attrs=['reverse', 'blink']))
