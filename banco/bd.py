from mysql.connector import connect
from contextlib import contextmanager
import sys
sys.path.append("../")
from defaults import BD_PARAMETER

# o context serve para utilizar o with, ou seja que sempre
# terá a conexão aberta até enquanto tiver no escopo e destroi sozinho

@contextmanager
def conection():
    connection = connect(**BD_PARAMETER)
    try:
        yield connection
    finally:
        if (connection and connection.is_connected()):
            connection.close()
