from mysql.connector import connect
from contextlib import contextmanager
from manga_extractor.core.defaults import BD_PARAMETER




@contextmanager
def conection():
    connection = connect(**BD_PARAMETER)
    try:
        yield connection
    finally:
        if (connection and connection.is_connected()):
            connection.close()
