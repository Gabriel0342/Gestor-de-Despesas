from http.client import responses
from datetime import date
from webbrowser import get
from xmlrpc.client import boolean
import bcrypt
from supabase import create_client, Client

login = False
IdUtilizador = 0
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

    passwordBytes = password.encode("utf-8")
    hashed_password = bcrypt.hashpw(passwordBytes, bcrypt.gensalt())

    datacreate = date.today()
    loginvalido: bool = True

    # garantir email único
    responde = supabase_cliente.table("utilizador").select("idutilizador").eq('email', email).execute()
    while len(responde.data) > 0:
        print("Email já utilizado")
        email = input("Qual o seu Email: ")
        responde = supabase_cliente.table("utilizador").select("idutilizador").eq('email', email).execute()

    dados = {
        "nome": nome,
        "email": email,
        "password": hashed_password.decode("utf-8"),
        "datacreate": datacreate.strftime('%Y-%m-%d'),
        "loginvalido": loginvalido,
    }

    resp_user = supabase_cliente.table("utilizador").insert(dados).execute()
    novo_id = resp_user.data[0]["idutilizador"]

    agora = date.today()
    mes = agora.month
    ano = agora.year

    dados2 = {
        "idutilizador": novo_id,
        "valor": 0,
        "mes": mes,
        "ano": ano
    }

    resp_orc = supabase_cliente.table("orcamento").insert(dados2).execute()

def eliminarUtilizador(nome):
    response = supabase_cliente.table("utilizador").update({"loginvalido": False}).eq("nome",nome).execute()

def login():
    global IdUtilizador
    global login
    userName = input("Qual o seu UserName: ")
    password = input("Qual a sua password: ")

    response = supabase_cliente.table("utilizador").select("password").eq("nome",userName).single().execute() #vai buscar a password

    verificarPassword = bcrypt.checkpw(password.encode("utf-8"), response.data["password"].encode("utf-8"))#compara a password

    if(verificarPassword):
        print("Login Válido", userName)
        login = True
        response = supabase_cliente.table("utilizador").select("idutilizador").eq("nome",userName).single().execute()
        IdUtilizador = response.data["idutilizador"]
def criarDespesas():
    global IdUtilizador
    tiposDespesas = ('1-Alimentação','2-Habitação','3-Transportes','4-Saúde','5-Comunicação','6-Jogos','7-Tecnologia','8-Outros')
    print("Qual o ID do tipo de Despesa? ")
    for tipoDespesa in tiposDespesas:
        print("\t",tipoDespesa)
    tipoDespesas = int(input(": "))
    valor = float(input("Qual o valor? "))
    descricao = str(input("Descricao: "))
    data = date.today()

    dados = {
        "idutilizador": IdUtilizador,
        "data":data.isoformat(),
        "idcategoria":tipoDespesas,
        "valorgasto":valor,
        "descricao":descricao,
    }
    response = supabase_cliente.table("despesas").insert(dados).execute()

    responses = supabase_cliente.table("orcamento").select("valor").eq("idutilizador", IdUtilizador).single().execute()

    valorOrcamento = responses.data["valor"]

    valorNovo = valorOrcamento - valor
    response = supabase_cliente.table("orcamento").update({"valor": valorNovo}).eq("idutilizador",IdUtilizador).execute()

    print("Despesa Criada com sucesso!")

def listaDespesas(IdUtilizador):
    response = supabase_cliente.table("despesas").select("*").eq("idutilizador",IdUtilizador).execute()
    print(response.data)
def eliminarDespesas(IdUtilizador,IdDespesas):
    response = supabase_cliente.table("despesas").eq("idutilizador",IdUtilizador,"iddespesas",IdDespesas).delete()

def ganho():
    valor = float(input("Claro!\nQual o valor do ganho?:"))
    responses = supabase_cliente.table("orcamento").select("valor").eq("idutilizador",IdUtilizador).single().execute()

    valorOrcamento = responses.data["valor"]

    valorNovo = valorOrcamento + valor
    response = supabase_cliente.table("orcamento").update({"valor": valorNovo}).eq("idutilizador",IdUtilizador).execute()
def valorGastoTipoDespesa():
    categoria = str(input("Categoria: "))
    responses = supabase_cliente.table("categoria").select("idcategoria").eq("categoria", categoria).single().execute()
    idCategoria = responses.data["idcategoria"]
    responses = supabase_cliente.table("despesas").select("*").eq("idcategoria",idCategoria).execute()
    print(responses.data)

def listaDespesasPorPeriodo(IdUtilizador,ano,mes):
    #Filtro de datas
    dataInicio = date(ano,mes,1) # primeiro dia do mes que queremos filtrar
    if mes == 12:
        dataFim = date(ano+1,1,1) # caso o mes seja Dezembro o filtro vai inculir o dia 1 de janeiro
    else:
        dataFim = date(ano,mes+1,1) # aplica o filtro até ao primeiro dia do proximo mes

    response = (((supabase_cliente.table("despesas").select("*").eq("idutilizador",IdUtilizador).
                gte("data",dataInicio.isoformat())).#datas >= à dataInicio
                lt("data",dataFim.isoformat())).#datas < à dataFim
                execute())
    if (response.data):
        print(response.data)
    else:
        print("Não temos despesas nesse periodo")
def orcamentoMes(mes,ano):
    responses = supabase_cliente.table("orcamento").select("valor").eq("mes",mes).eq("ano",ano).execute()
    if len(responses.data) > 0:
        print(responses.data)
    else:
        print("Não tenho despesas nesse mês!")

#Funcionamento do Sistema

url: str = "https://dyaqsxvflvbetwwxmehr.supabase.co"
key: str = "sb_secret_xBi5p84ypNR9-Jq7Jn5I2Q_I29odZSx"
supabase_cliente: Client = create_client(url, key)

conta = str(input("Você já tem conta?[S/N] : ")).upper()
if(conta == "S"):
    login()
else:
    print("Tem de criar Conta no sistema")
    criarUtilizadores()


if login == True:
    orcamentoMes(12,2025)

else:
    print("Verifique as suas credenciais!")
    login()