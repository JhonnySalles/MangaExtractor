from mysql.connector.errors import ProgrammingError
from .bd import conection

sql = """
    CREATE TABLE IF NOT EXISTS %s (
        id INT NOT NULL AUTO_INCREMENT,
        manga LONGTEXT NOT NULL,
        volume INT(4) NOT NULL,
        capitulo INT(11) NOT NULL,
        nome_pagina VARCHAR(250) NOT NULL,
        numero_pagina INT(11),
        linguagem VARCHAR(4),
        sequencia_texto INT(4),
        texto LONGTEXT NOT NULL,
        posicao_x1 double DEFAULT NULL,
        posicao_y1 double DEFAULT NULL,
        posicao_x2 double DEFAULT NULL,
        posicao_y2 double DEFAULT NULL,
        hash_pagina VARCHAR(250),
        scan VARCHAR(250),
        is_raw BOOLEAN, PRIMARY KEY (id)
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
            cursor.execute(sql % tabela)
            conexao.commit()
        except ProgrammingError as e:
            print(f'Erro na criação da tabela: {e.msg}')
        
        return tabela