from mysql.connector import connect
from mysql.connector.errors import ProgrammingError
from contextlib import contextmanager

parametros = dict(
    host='localhost',
    port=3306,
    user='admin',
    passwd='admin',
    database='manga_extractor'
)

#o context serve para utilizar o with, ou seja que sempre
#terá a conexão aberta até enquanto tiver no escopo e destroi sozinho
@contextmanager
def conection():
    conexao = connect(**parametros)
    try:
        yield conexao
    finally:
        if (conexao and conexao.is_connected()):
            conexao.close()