from mysql.connector import connect
from contextlib import contextmanager
import sys
sys.path.append("../")
from defaults import PARAMETROS_BD

# o context serve para utilizar o with, ou seja que sempre
# terá a conexão aberta até enquanto tiver no escopo e destroi sozinho

@contextmanager
def conection():
    conexao = connect(**PARAMETROS_BD)
    try:
        yield conexao
    finally:
        if (conexao and conexao.is_connected()):
            conexao.close()
