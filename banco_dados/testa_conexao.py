from bd import  conection

with conection() as conexao:
    if conexao.is_connected():
        print('Conectado ao banco de dados!')