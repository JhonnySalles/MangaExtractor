import sqlite3
import re

class SQLiteCursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor
        self._results = []
        self._index = 0

    @property
    def rowcount(self):
        if hasattr(self, '_rowcount'):
            return self._rowcount
        return self.cursor.rowcount

    def execute(self, sql, params=None):
        # Translate MySQL specific DELETE alias FROM table AS alias
        sql = re.sub(r'DELETE \w+ FROM ([\w`{}_]+) AS \w+', r'DELETE FROM \1', sql, flags=re.IGNORECASE)
        
        # Translate double quoted strings to single quoted strings for SQLite
        # Handle variations with spaces: ="..." or = "..." or IN ("...")
        sql = re.sub(r'=\s*"([^"]+)"', r"='\1'", sql)
        sql = re.sub(r'=\s*\'([^\']+)\'', r"='\1'", sql) # Normalize single quotes
        sql = re.sub(r'IN\s*\(\s*"([^"]+)"\s*\)', r"IN ('\1')", sql, flags=re.IGNORECASE)
        sql = re.sub(r"IN\s*\(\s*'([^']+)'\s*\)", r"IN ('\1')", sql, flags=re.IGNORECASE)

        # Convert remaining %s to ?
        sql = sql.replace('"%s"', '?').replace("'%s'", '?').replace('%s', '?')
        
        if 'CALL sp_create_table' in sql:
            return

        # Mock information_schema.tables for existTable
        if 'information_schema.tables' in sql.lower():
            match = re.search(r'LIKE ["\'](.+)_textos["\']', sql)
            if match:
                table_prefix = match.group(1)
                sql = f"SELECT name FROM sqlite_master WHERE type='table' AND name = '{table_prefix}_textos'"
            else:
                sql = "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_textos'"
            params = None

        # Execute
        if params:
            clean_params = tuple(str(p) for p in params)
            self.cursor.execute(sql, clean_params)
        else:
            self.cursor.execute(sql)
        
        if sql.strip().upper().startswith('SELECT'):
            results = self.cursor.fetchall()
            self._results = results
            self._rowcount = len(results)
            self._index = 0
        else:
            if hasattr(self, '_rowcount'):
                delattr(self, '_rowcount')
            self._results = []
            self._index = 0

    def fetchone(self):
        if self._index < len(self._results):
            res = self._results[self._index]
            self._index += 1
            return res
        return self.cursor.fetchone()

    def fetchall(self):
        if self._results:
            return self._results
        return self.cursor.fetchall()

    def __iter__(self):
        return self

    def __next__(self):
        res = self.fetchone()
        if res is None:
            raise StopIteration
        return res

    def close(self):
        self.cursor.close()

class SQLiteConnWrapper:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def cursor(self, buffered=False):
        return SQLiteCursorWrapper(self.conn.cursor())

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def is_connected(self):
        return True

def setup_sqlite_memory_db(base):
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    
    # Create tables
    tables = [
        f"CREATE TABLE {base}_volumes (id TEXT PRIMARY KEY, manga TEXT, volume TEXT, linguagem TEXT)",
        f"CREATE TABLE {base}_capitulos (id TEXT PRIMARY KEY, id_volume TEXT, manga TEXT, volume TEXT, capitulo TEXT, linguagem TEXT, scan TEXT, is_extra BOOLEAN, is_raw BOOLEAN)",
        f"CREATE TABLE {base}_paginas (id TEXT PRIMARY KEY, id_capitulo TEXT, nome TEXT, numero INTEGER, hash_pagina TEXT)",
        f"CREATE TABLE {base}_textos (id TEXT PRIMARY KEY, id_pagina TEXT, sequencia INTEGER, texto TEXT, posicao_x1 INTEGER, posicao_y1 INTEGER, posicao_x2 INTEGER, posicao_y2 INTEGER, versao_app TEXT)",
        f"CREATE TABLE {base}_vocabularios (id TEXT PRIMARY KEY, id_pagina TEXT, id_capitulo TEXT, texto TEXT)",
        f"CREATE TABLE {base}_capas (id TEXT PRIMARY KEY, id_volume TEXT, manga TEXT, volume TEXT, linguagem TEXT, arquivo TEXT, extensao TEXT, capa BLOB)"
    ]
    
    for table in tables:
        cursor.execute(table)
    
    conn.commit()
    return conn
