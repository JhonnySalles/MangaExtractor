from mysql.connector.errors import ProgrammingError
from bd import conection

select = 'SELECT id FROM %s WHERE manga = %s AND volume = %s AND capitulo = %s AND nome_pagina = %s AND texto = %s '
insert = """
    INSERT INTO %s (manga, volume, capitulo, nome_pagina, numero_pagina, linguagem, sequencia_texto, texto,
        posicao_x1, posicao_y1, posicao_x2, posicao_y2, hash_pagina, scan, is_raw) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""
update = """
    UPDATE %s SET manga = %s, volume = %s, capitulo = %s, nome_pagina = %s, numero_pagina = %s, linguagem = %s,
        sequencia_texto = %s, texto = %s, posicao_x1 = %s, posicao_y1 = %s, posicao_x2 = %s, posicao_y2 = %s,
        hash_pagina = %s, scan = %s, is_raw = %s
    WHERE campo = %s
"""

def insereDados(tabela='', dados=None, where=None):
    with conection() as conexao:
        if tabela is '' :
            raise ValueError("Erro ao gravar os dados, tabela não informada.")
        elif dados is None:
            raise ValueError("Erro ao gravar os dados, dados para inserção vazio.")   

        try :
            args = (f'{tabela}',where)
            cursor = conexao.cursor()
            cursor.execute(select, args)

            if where is None:
                args = (f'{tabela}',dados)
            else:
                args = (f'{tabela}',dados,where)

            if cursor.rowcount > 0:
                try:
                    args = (f'{texto}',)
                    cursor.execute(update, args)
                    conexao.commit()
                except ProgrammingError as e:
                    print(f'Erro ao gravar os dados: {e.msg}')
                else:
                    print(f'{cursor.rowcount} registro(s) atualizado com sucesso.', args)
            else:
                try:
                    args = (f'{texto}',)
                    cursor.execute(insert, args)
                    conexao.commit()
                except ProgrammingError as e:
                    print(f'Erro ao gravar os dados: {e.msg}')
                else:
                    print(f'{cursor.rowcount} registro(s) inserido com sucesso.', args)
        except ProgrammingError as e:
            print(f'Erro ao gravar os dados: {e.msg}')
