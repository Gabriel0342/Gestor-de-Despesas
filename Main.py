from http.client import responses
from datetime import date
from xmlrpc.client import boolean

from supabase import create_client, Client
#CRUDE
def listarUtilizadores():
    response = supabase_cliente.table("utilizador").select("*").execute()
    dados = response.data
    for i in dados:
        print(i)
def criarUtilizadores():
    nome = input("Qual o seu UserName: ")
    email = input("Qual o seu Email: ")
    password = input("Qual a sua password: ")
    datacreate = date.today()
    loginvalido : bool = True

    responde = supabase_cliente.table("utilizador").select("idutilizador").eq('email',email).execute()
    while(len(responde.data) > 0):
        print("Email já utilizado")
        email = input("Qual o seu Email: ")
        responde = supabase_cliente.table("utilizador").select("idutilizador").eq('email', email).execute()

    dados = {"nome": nome,
             "email": email,
             "password" : password,
             "datacreate" : datacreate.strftime('%Y-%m-%d'),
             "loginvalido": loginvalido,
             }

    response = supabase_cliente.table("utilizador").insert(dados).execute()
def eliminarUtilizadores(nome):
    response = supabase_cliente.table("utilizador").delete().eq("nome",nome).execute()
def alterarUtilizadores(estado,nome):
    response = supabase_cliente.table("utilizador").update({"loginvalido": estado}).eq("nome",nome).execute()



url: str = "https://dyaqsxvflvbetwwxmehr.supabase.co"
key: str = "sb_secret_xBi5p84ypNR9-Jq7Jn5I2Q_I29odZSx"
supabase_cliente: Client = create_client(url, key)



