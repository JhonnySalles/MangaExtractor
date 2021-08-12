from mysql.connector.errors import ProgrammingError
from bd import conection

sql = """
    CREATE TABLE IF NOT EXIST %s (
        id INT NOT NULL AUTO_INCREMENT,
        manga LONGTEXT NOT NULL,
        volume INT(4) NOT NULL,
        capitulo INT(11) NOT NULL,
        nome_pagina VARCHAR(250) NOT NULL,
        numero_pagina INT(11),
        linguagem VARCHAR(4),
        sequencia_texto INT(4),
        texto LONGTEXT NOT NULL,
        posicao_x1 INT(11),
        posicao_y1 INT(11),
        posicao_x2 INT(11),
        posicao_y2 INT(11),
        hash_pagina VARCHAR(250),
        scan VARCHAR(250),
        is_raw BOOLEAN, PRIMARY KEY (id)
    ) CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; 
"""
def criaTabela(tabela=''):
    with conection() as conexao:
        if tabela is '' :
            raise ValueError("Erro na criação da tabela, tabela não informada.")

        try:
            args = (f'{tabela}',)
            cursor = conexao.cursor()
            cursor.execute(sql, args)
        except ProgrammingError as e:
            print(f'Erro na criação da tabela: {e.msg}')