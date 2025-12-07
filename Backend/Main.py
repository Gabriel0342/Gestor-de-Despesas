from datetime import date
import os
import bcrypt
from fastapi import FastAPI, HTTPException, Query, Path
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://dyaqsxvflvbetwwxmehr.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_secret_xBi5p84ypNR9-Jq7Jn5I2Q_I29odZSx")

supabase_cliente: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

# ----------------- MODELOS Pydantic ----------------- #

class UserCreate(BaseModel):
    nome: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    nome: str
    password: str

class DespesaCreate(BaseModel):
    idcategoria: int
    valorgasto: float
    descricao: str

@app.get("/utilizadores")
def listar_utilizadores():
    resp = supabase_cliente.table("utilizador").select("*").execute()
    return resp.data

@app.post("/utilizadores", status_code=201)
def criar_utilizador(body: UserCreate):
    # garantir email único
    existe = (
        supabase_cliente
        .table("utilizador")
        .select("idutilizador")
        .eq("email", body.email)
        .execute()
    )
    if len(existe.data) > 0:
        raise HTTPException(status_code=400, detail="Email já utilizado")

    password_bytes = body.password.encode("utf-8")
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

    datacreate = date.today()

    dados_user = {
        "nome": body.nome,
        "email": body.email,
        "password": hashed_password,
        "datacreate": datacreate.strftime("%Y-%m-%d"),
        "loginvalido": True,
    }

    resp_user = supabase_cliente.table("utilizador").insert(dados_user).execute()
    novo_id = resp_user.data[0]["idutilizador"]

    agora = date.today()
    dados_orc = {
        "idutilizador": novo_id,
        "valor": 0,
        "mes": agora.month,
        "ano": agora.year,
    }
    supabase_cliente.table("orcamento").insert(dados_orc).execute()

    return {"idutilizador": novo_id, "message": "Utilizador criado com sucesso"}

@app.post("/login")
def login(body: UserLogin):
    resp = (
        supabase_cliente
        .table("utilizador")
        .select("idutilizador, password, loginvalido")
        .eq("nome", body.nome)
        .single()
        .execute()
    )

    if not resp.data or not resp.data["loginvalido"]:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    hash_bd = resp.data["password"].encode("utf-8")
    ok = bcrypt.checkpw(body.password.encode("utf-8"), hash_bd)
    if not ok:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    # Aqui poderias devolver um JWT; por agora devolve só o id
    return {"idutilizador": resp.data["idutilizador"], "message": "Login válido"}

@app.patch("/utilizadores/{nome}")
def desativar_utilizador(nome: str = Path(...)):
    resp = (
        supabase_cliente
        .table("utilizador")
        .update({"loginvalido": False})
        .eq("nome", nome)
        .execute()
    )
    if len(resp.data) == 0:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    return {"message": "Utilizador desativado"}

@app.post("/utilizadores/{idutilizador}/despesas", status_code=201)
def criar_despesas(idutilizador: int = Path(...),body: DespesaCreate = ...):
    hoje = date.today().isoformat()

    dados = {
        "idutilizador": idutilizador,
        "data": hoje,
        "idcategoria": body.idcategoria,
        "valorgasto": body.valorgasto,
        "descricao": body.descricao,
    }

    supabase_cliente.table("despesas").insert(dados).execute()

    # atualizar orçamento
    resp_orc = (
        supabase_cliente
        .table("orcamento")
        .select("valor")
        .eq("idutilizador", idutilizador)
        .single()
        .execute()
    )

    if not resp_orc.data:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")

    valor_orc = resp_orc.data["valor"]
    valor_novo = valor_orc - body.valorgasto

    supabase_cliente.table("orcamento").update(
        {"valor": valor_novo}
    ).eq("idutilizador", idutilizador).execute()

    return {"message": "Despesa criada com sucesso", "valor_orcamento_atual": valor_novo}

@app.get("/utilizadores/{idutilizador}/despesas")
def listar_despesas(idutilizador: int = Path(...)):
    resp = (
        supabase_cliente
        .table("despesas")
        .select("*")
        .eq("idutilizador", idutilizador)
        .execute()
    )
    return resp.data

@app.delete("/utilizadores/{idutilizador}/despesas/{iddespesas}")
def eliminar_despesa(idutilizador: int = Path(...),iddespesas: int = Path(...)):
    resp = (
        supabase_cliente
        .table("despesas")
        .eq("idutilizador", idutilizador)
        .eq("iddespesas", iddespesas)
        .delete()
        .execute()
    )
    if len(resp.data) == 0:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")
    return {"message": "Despesa eliminada"}

@app.post("/utilizadores/{idutilizador}/depositos")
def criar_deposito(idutilizador: int = Path(...),valor: float = Query(..., gt=0)):
    resp_orc = (
        supabase_cliente
        .table("orcamento")
        .select("valor")
        .eq("idutilizador", idutilizador)
        .single()
        .execute()
    )

    if not resp_orc.data:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")

    valor_atual = resp_orc.data["valor"]
    valor_novo = valor_atual + valor

    supabase_cliente.table("orcamento").update(
        {"valor": valor_novo}
    ).eq("idutilizador", idutilizador).execute()

    return {"message": "Depósito registado", "valor_orcamento_atual": valor_novo}

@app.get("/utilizadores/{idutilizador}/despesas/por-tipo")
def despesas_por_tipo(idutilizador: int = Path(...),categoria: str = Query(...)):
    resp_cat = (
        supabase_cliente
        .table("categoria")
        .select("idcategoria")
        .eq("categoria", categoria)
        .single()
        .execute()
    )
    if not resp_cat.data:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    idcat = resp_cat.data["idcategoria"]

    resp = (
        supabase_cliente
        .table("despesas")
        .select("*")
        .eq("idutilizador", idutilizador)
        .eq("idcategoria", idcat)
        .execute()
    )
    return resp.data

@app.get("/utilizadores/{idutilizador}/despesas/periodo")
def despesas_por_periodo(idutilizador: int = Path(...),ano: int = Query(...),mes: int = Query(..., ge=1, le=12),):
    data_inicio = date(ano, mes, 1)
    if mes == 12:
        data_fim = date(ano + 1, 1, 1)
    else:
        data_fim = date(ano, mes + 1, 1)

    resp = (
        supabase_cliente
        .table("despesas")
        .select("*")
        .eq("idutilizador", idutilizador)
        .gte("data", data_inicio.isoformat())
        .lt("data", data_fim.isoformat())
        .execute()
    )

    if not resp.data:
        return {"message": "Não existem despesas nesse período", "despesas": []}
    return {"despesas": resp.data}

@app.get("/orcamento-mensal")
def orcamento_mensal(mes: int = Query(..., ge=1, le=12),ano: int = Query(...),):
    resp = (
        supabase_cliente
        .table("orcamento")
        .select("idutilizador, valor")
        .eq("mes", mes)
        .eq("ano", ano)
        .execute()
    )
    if len(resp.data) == 0:
        return {"message": "Não tenho despesas nesse mês!", "orcamentos": []}
    return {"orcamentos": resp.data}
