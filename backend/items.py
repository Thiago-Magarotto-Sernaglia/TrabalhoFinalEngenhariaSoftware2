import os
from typing import AsyncGenerator
import asyncpg
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from contextlib import asynccontextmanager


# URL de conexão com o Postgres (ex.: postgres://user:pass@host:port/dbname)
DATABASE_URL = os.getenv("DATABASE_URL", "postgres://postgres:password@localhost:5432/bd_soft_2")


# Variável global para o pool (inicializada no lifespan)
_db_pool: asyncpg.pool.Pool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Executado no startup antes do app começar a servir e no shutdown após parar.
    Aqui criamos o pool de conexões e garantimos que ele será fechado corretamente.
    """
    global _db_pool
    # cria um pool de conexões asyncpg
    _db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)

    # opcional: criar tabelas iniciais (idempotente)
    async with _db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS exemplo (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS vendedor (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                gerente_id INTEGER REFERENCES gerente(id)
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS cliente (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                vendedor_id INTEGER REFERENCES vendedor(id)
            );
        """)

    try:
        # yield permite que a aplicação rode normalmente entre startup e shutdown
        yield
    finally:
        # fecha o pool ao encerrar a aplicação
        if _db_pool:
            await _db_pool.close()

# cria a app passando o lifespan
app = FastAPI(lifespan=lifespan)


#####################################################
#
# Dependência: fornece uma conexão por requisição
#
########################################
async def get_conn() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Dependência que fornece uma conexão do pool para o endpoint.
    Usa 'acquire' para pegar a conexão e 'release' é automático ao sair do contexto.
    """
    if _db_pool is None:
        # se o pool não estiver pronto, erro 500
        raise HTTPException(status_code=500, detail="Pool de banco não inicializado")
    async with _db_pool.acquire() as conn:
        yield conn


######################################################################
#
# Endpoints adicionando, listando e removendo items do banco de dados elementos ao banco de dados
#
######################################################################
@app.post("/itens")
async def criar_item(nome: str, conn: asyncpg.Connection = Depends(get_conn)):
    """
    Insere um registro simples e retorna o id.
    A transação é opcional; aqui usamos execute + fetchrow para retornar o id.
    """
    row = await conn.fetchrow(
        "INSERT INTO exemplo (nome) VALUES ($1) RETURNING id",
        nome
    )
    return {"id": row["id"]}


@app.get("/itens/{item_id}")
async def obter_item_por_id(item_id: int, conn: asyncpg.Connection = Depends(get_conn)):
    """
    Busca um item pelo id (path param).
    Retorna 404 se não encontrado.
    """
    row = await conn.fetchrow("SELECT id, nome FROM exemplo WHERE id = $1", item_id)
    if not row:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return dict(row)

@app.get("/itens")
async def listar_itens(conn: asyncpg.Connection = Depends(get_conn)):
    """
    Lista todos os registros da tabela 'exemplo'.
    fetch retorna uma lista de Record; convertendo para dict para serializar.
    """
    rows = await conn.fetch("SELECT id, nome FROM exemplo ORDER BY id")
    return [dict(r) for r in rows]

# -------------------------
# Execução local (teste)
# -------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)