import os
import asyncio
import asyncpg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()
_db_pool: asyncpg.pool.Pool | None = None

# Schemas
class GerenteIn(BaseModel):
    nome: str
    email: EmailStr

class VendedorIn(BaseModel):
    nome: str
    email: EmailStr
    gerente_id: int | None = None

class ClienteIn(BaseModel):
    nome: str
    email: EmailStr
    vendedor_id: int | None = None

# Startup / shutdown: cria pool
@app.on_event("startup")
async def startup():
    global _db_pool
    _db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)

    async with _db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS gerente (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
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

@app.on_event("shutdown")
async def shutdown():
    global _db_pool
    if _db_pool:
        await _db_pool.close()

# Funções de acesso ao DB
async def add_gerente(conn: asyncpg.Connection, g: GerenteIn) -> int:
    row = await conn.fetchrow(
        "INSERT INTO gerente (nome, email) VALUES ($1, $2) RETURNING id",
        g.nome, g.email
    )
    return row["id"]

async def add_vendedor(conn: asyncpg.Connection, v: VendedorIn) -> int:
    row = await conn.fetchrow(
        "INSERT INTO vendedor (nome, email, gerente_id) VALUES ($1, $2, $3) RETURNING id",
        v.nome, v.email, v.gerente_id
    )
    return row["id"]

async def add_cliente(conn: asyncpg.Connection, c: ClienteIn) -> int:
    row = await conn.fetchrow(
        "INSERT INTO cliente (nome, email, vendedor_id) VALUES ($1, $2, $3) RETURNING id",
        c.nome, c.email, c.vendedor_id
    )
    return row["id"]

# Endpoints simples
@app.post("/gerentes")
async def criar_gerente(payload: GerenteIn):
    async with _db_pool.acquire() as conn:
        try:
            async with conn.transaction():
                gid = await add_gerente(conn, payload)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Email de gerente já cadastrado")
    return {"id": gid}

@app.post("/vendedores")
async def criar_vendedor(payload: VendedorIn):
    async with _db_pool.acquire() as conn:
        # opcional: verificar existência do gerente se gerente_id for fornecido
        if payload.gerente_id is not None:
            exists = await conn.fetchval("SELECT 1 FROM gerente WHERE id=$1", payload.gerente_id)
            if not exists:
                raise HTTPException(status_code=404, detail="Gerente não encontrado")
        try:
            async with conn.transaction():
                vid = await add_vendedor(conn, payload)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Email de vendedor já cadastrado")
    return {"id": vid}

@app.post("/clientes")
async def criar_cliente(payload: ClienteIn):
    async with _db_pool.acquire() as conn:
        # opcional: verificar existência do vendedor se vendedor_id for fornecido
        if payload.vendedor_id is not None:
            exists = await conn.fetchval("SELECT 1 FROM vendedor WHERE id=$1", payload.vendedor_id)
            if not exists:
                raise HTTPException(status_code=404, detail="Vendedor não encontrado")
        try:
            async with conn.transaction():
                cid = await add_cliente(conn, payload)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Email de cliente já cadastrado")
    return {"id": cid}

# Endpoint de exemplo para listar clientes (com JOIN simples)
@app.get("/clientes")
async def listar_clientes():
    async with _db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT c.id, c.nome, c.email,
                   v.id AS vendedor_id, v.nome AS vendedor_nome,
                   g.id AS gerente_id, g.nome AS gerente_nome
            FROM cliente c
            LEFT JOIN vendedor v ON c.vendedor_id = v.id
            LEFT JOIN gerente g ON v.gerente_id = g.id
            ORDER BY c.id
        """)
        return [dict(r) for r in rows]

# Execução local (uvicorn)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
