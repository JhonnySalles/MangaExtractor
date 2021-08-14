from PySimpleGUI.PySimpleGUI import No
from mysql.connector.errors import ProgrammingError
from .bd import conection

volumes = """
    CREATE TABLE IF NOT EXISTS %s_volumes (
        id INT NOT NULL AUTO_INCREMENT,
        manga LONGTEXT NOT NULL,
        volume INT(4) NOT NULL,
        capitulo INT(11) NOT NULL,
        nome_pagina VARCHAR(250) NOT NULL,
        numero_pagina INT(11),
        linguagem VARCHAR(4),
        hash_pagina VARCHAR(250),
        scan VARCHAR(250),
        is_raw BOOLEAN, PRIMARY KEY (id)
    ) CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; 
"""
textos = """
    CREATE TABLE IF NOT EXISTS %s_textos (
        id INT NOT NULL AUTO_INCREMENT,
        id_volume INT(11) NOT NULL,
        sequencia INT(4),
        texto LONGTEXT NOT NULL,
        posicao_x1 double DEFAULT NULL,
        posicao_y1 double DEFAULT NULL,
        posicao_x2 double DEFAULT NULL,
        posicao_y2 double DEFAULT NULL, PRIMARY KEY (id),
        KEY %s_volumes_%s_textos_fk (id_volume),
        CONSTRAINT %s_volumes_%s_textos_fk FOREIGN KEY (id_volume) REFERENCES %s_volumes (id) ON DELETE CASCADE ON UPDATE CASCADE
    ) CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

tabela = ''
def criaTabela(nome=None):
    with conection() as conexao:
        if nome == None :
            raise ValueError("Erro na criação da tabela, tabela não informada.")

        tabela = nome.replace(" ", "_")
        try:
            cursor = conexao.cursor()
            cursor.execute(volumes % tabela)
            conexao.commit()
        except ProgrammingError as e:
            print(f'Erro na criação da tabela volume: {e.msg}')

        try:
            cursor = conexao.cursor()
            cursor.execute(textos % (tabela, tabela, tabela, tabela, tabela, tabela))
            conexao.commit()
        except ProgrammingError as e:
            print(f'Erro na criação da tabela texto: {e.msg}')
        
        return tabela

def testaConexao():
    with conection() as conexao:
        if conexao.is_connected():
            print('Conectado ao banco de dados!')
        return conexao.is_connected()

selectTexto = 'SELECT id FROM {} WHERE id_volume = %s AND texto = %s '
insertTexto = """
    INSERT INTO {} (id_volume, sequencia, texto, posicao_x1, posicao_y1, posicao_x2, posicao_y2) 
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""
updateTexto = """
    UPDATE {} SET sequencia = %s, texto = %s, posicao_x1 = %s, posicao_y1 = %s, posicao_x2 = %s, posicao_y2 = %s
    WHERE id = %s
"""

def gravaTexto(operacao=None, id_volume=None, texto=None):
    with conection() as conexao:
        if operacao.base is None :
            raise ValueError("Erro ao gravar os dados, tabela não informada.")
        elif id_volume is None:
            raise ValueError("Erro ao gravar os dados, não informado id.")   
        elif texto is None:
            raise ValueError("Erro ao gravar os dados, dados para inserção vazio.") 

        try :
            args = (id_volume, texto.texto)
            cursor = conexao.cursor(buffered=True)
            sql = selectTexto.format(operacao.base + '_textos')
            cursor.execute(sql, args)

            if cursor.rowcount > 0:
                try:
                    args = (texto.sequencia, texto.texto, texto.posX1, texto.posY1, 
                            texto.posX2, texto.posY2, cursor.fetchone()[0])
                    sql = updateTexto.format(operacao.base + '_textos')
                    cursor.execute(sql, args)
                    conexao.commit()
                except ProgrammingError as e:
                    print(f'Erro ao atualizar os dados: {e.msg}')
            else:
                try:
                    args = (id_volume, texto.sequencia, texto.texto, texto.posX1, 
                            texto.posY1, texto.posX2, texto.posY2)
                    sql = insertTexto.format(operacao.base + '_textos')
                    cursor.execute(sql, args)
                    conexao.commit()
                except ProgrammingError as e:
                    print(f'Erro ao gravar os dados: {e.msg}')

        except ProgrammingError as e:
            print(f'Erro ao consultar registro: {e.msg}')

selectVolume = 'SELECT id FROM {} WHERE manga = %s AND volume = %s AND capitulo = %s AND nome_pagina = %s '
insertVolume = """
    INSERT INTO {} (manga, volume, capitulo, nome_pagina, numero_pagina, linguagem, hash_pagina, scan, is_raw) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""
updateVolume = """
    UPDATE {} SET manga = %s, volume = %s, capitulo = %s, nome_pagina = %s, numero_pagina = %s, linguagem = %s,
        hash_pagina = %s, scan = %s, is_raw = %s
    WHERE id = %s
"""

def gravaManga(operacao=None, manga=None):
    with conection() as conexao:
        if operacao.base is None :
            raise ValueError("Erro ao gravar os dados, tabela não informada.")
        elif manga is None:
            raise ValueError("Erro ao gravar os dados, dados para inserção vazio.")   

        try :
            id = None
            args = (manga.nome, manga.volume, manga.capitulo, manga.nomePagina)
            cursor = conexao.cursor(buffered=True)
            sql = selectVolume.format(operacao.base + '_volumes')
            cursor.execute(sql, args)

            if cursor.rowcount > 0:
                try:
                    id = cursor.fetchone()[0]
                    args = (manga.nome, manga.volume, manga.capitulo, manga.nomePagina, 
                            manga.numeroPagina, manga.linguagem, manga.hashPagina, manga.scan,
                            manga.isScan, id)
                    sql = updateVolume.format(operacao.base + '_volumes')
                    cursor.execute(sql, args)
                    conexao.commit()
                except ProgrammingError as e:
                    print(f'Erro ao atualizar os dados: {e.msg}')
                else:
                    print(f'{cursor.rowcount} registro(s) atualizado com sucesso.', args)
            else:
                try:
                    args = (manga.nome, manga.volume, manga.capitulo, manga.nomePagina, 
                            manga.numeroPagina, manga.linguagem, manga.hashPagina, manga.scan, manga.isScan)
                    sql = insertVolume.format(operacao.base + '_volumes')
                    cursor.execute(sql, args)
                    conexao.commit()
                    id = cursor.lastrowid
                except ProgrammingError as e:
                    print(f'Erro ao gravar os dados: {e.msg}')
                else:
                    print(f'{cursor.rowcount} registro(s) inserido com sucesso.', args)

            
            for texto in manga.textos:
                try:
                    gravaTexto(operacao, id, texto)
                except ProgrammingError as e:
                    print(f'{e.msg}')

        except ProgrammingError as e:
            print(f'Erro ao consultar registro: {e.msg}')

def gravarDados(operacao, processados):
    print('Gravando informações....')
    for manga in processados:
       gravaManga(operacao, manga)
    print('Gravação concluido.')