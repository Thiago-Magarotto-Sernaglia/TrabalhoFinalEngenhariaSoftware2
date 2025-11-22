# products.py
import os
import asyncio
import asyncpg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()
_db_pool: asyncpg.pool.Pool | None = None

# ---- Schemas ----
class CategoriaIn(BaseModel):
    nome: str

class ProdutoIn(BaseModel):
    nome: str
    preco: float
    unidade: str  # e.g., "kg", "un", "g", "l"
    categoria_id: int | None = None
    estoque: int = 0  # quantidade em estoque

class ProdutoUpdate(BaseModel):
    nome: str | None = None
    preco: float | None = None
    unidade: str | None = None
    categoria_id: int | None = None
    estoque: int | None = None

# ---- Startup / Shutdown (cria pool e tabelas) ----
@app.on_event("startup")
async def startup():
    global _db_pool
    _db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)

    async with _db_pool.acquire() as conn:
        # tabelas de categorias e produtos
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS categoria (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL UNIQUE
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS produto (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                preco NUMERIC NOT NULL,
                unidade TEXT NOT NULL,
                categoria_id INTEGER REFERENCES categoria(id),
                estoque INTEGER NOT NULL DEFAULT 0,
                UNIQUE(nome, categoria_id)
            );
        """)

        # Inserir categorias e produtos iniciais (se não existirem)
        await conn.execute("""
            INSERT INTO categoria (nome)
            SELECT v FROM (VALUES ('frutas'), ('verduras'), ('hortifruti'), ('laticinios'), ('bebidas')) AS t(v)
            ON CONFLICT (nome) DO NOTHING;
        """)

        # Exemplo: inserir alguns produtos iniciais sem duplicar
        await conn.execute("""
            INSERT INTO produto (nome, preco, unidade, categoria_id, estoque)
            SELECT p.nome, p.preco, p.unidade, c.id, p.estoque
            FROM (VALUES
                ('limão', 3.50, 'kg', 30),
                ('banana', 4.20, 'kg', 50),
                ('cenoura', 2.80, 'kg', 40),
                ('couve', 1.80, 'maço', 25)
            ) AS p(nome, preco, unidade, estoque)
            JOIN categoria c ON c.nome = CASE
                WHEN p.nome IN ('limão','banana') THEN 'frutas'
                WHEN p.nome IN ('cenoura','couve') THEN 'verduras'
                ELSE 'hortifruti'
            END
            ON CONFLICT (nome, categoria_id) DO NOTHING;
        """)

@app.on_event("shutdown")
async def shutdown():
    global _db_pool
    if _db_pool:
        await _db_pool.close()

# ---- Funções DB ----
async def add_categoria(conn: asyncpg.Connection, c: CategoriaIn) -> int:
    row = await conn.fetchrow(
        "INSERT INTO categoria (nome) VALUES ($1) RETURNING id",
        c.nome
    )
    return row["id"]

async def add_produto(conn: asyncpg.Connection, p: ProdutoIn) -> int:
    row = await conn.fetchrow(
        "INSERT INTO produto (nome, preco, unidade, categoria_id, estoque) VALUES ($1, $2, $3, $4, $5) RETURNING id",
        p.nome, p.preco, p.unidade, p.categoria_id, p.estoque
    )
    return row["id"]

async def get_produto(conn: asyncpg.Connection, pid: int):
    return await conn.fetchrow("SELECT * FROM produto WHERE id=$1", pid)

async def update_produto_db(conn: asyncpg.Connection, pid: int, u: ProdutoUpdate):
    # construir SQL dinamicamente conforme campos presentes
    cols = []
    vals = []
    idx = 1
    if u.nome is not None:
        cols.append(f"nome = ${idx}"); vals.append(u.nome); idx += 1
    if u.preco is not None:
        cols.append(f"preco = ${idx}"); vals.append(u.preco); idx += 1
    if u.unidade is not None:
        cols.append(f"unidade = ${idx}"); vals.append(u.unidade); idx += 1
    if u.categoria_id is not None:
        cols.append(f"categoria_id = ${idx}"); vals.append(u.categoria_id); idx += 1
    if u.estoque is not None:
        cols.append(f"estoque = ${idx}"); vals.append(u.estoque); idx += 1

    if not cols:
        return await conn.fetchrow("SELECT * FROM produto WHERE id=$1", pid)

    sql = "UPDATE produto SET " + ", ".join(cols) + f" WHERE id = ${idx} RETURNING *"
    vals.append(pid)
    return await conn.fetchrow(sql, *vals)

# ---- Endpoints categorias ----
@app.post("/categorias")
async def criar_categoria(payload: CategoriaIn):
    async with _db_pool.acquire() as conn:
        try:
            async with conn.transaction():
                cid = await add_categoria(conn, payload)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Categoria já existe")
    return {"id": cid}

@app.get("/categorias")
async def listar_categorias():
    async with _db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, nome FROM categoria ORDER BY nome")
        return [dict(r) for r in rows]

# ---- Endpoints produtos ----
@app.post("/produtos")
async def criar_produto(payload: ProdutoIn):
    async with _db_pool.acquire() as conn:
        # se categoria_id fornecido, verificar existência
        if payload.categoria_id is not None:
            exists = await conn.fetchval("SELECT 1 FROM categoria WHERE id=$1", payload.categoria_id)
            if not exists:
                raise HTTPException(status_code=404, detail="Categoria não encontrada")
        try:
            async with conn.transaction():
                pid = await add_produto(conn, payload)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Produto já cadastrado na mesma categoria")
    return {"id": pid}

@app.get("/produtos")
async def listar_produtos():
    async with _db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT p.id, p.nome, p.preco::text AS preco, p.unidade, p.estoque,
                   c.id AS categoria_id, c.nome AS categoria_nome
            FROM produto p
            LEFT JOIN categoria c ON p.categoria_id = c.id
            ORDER BY p.id
        """)
        # converter NUMERIC para string para evitar problemas de serialização
        return [dict(r) for r in rows]

@app.get("/produtos/{produto_id}")
async def obter_produto(produto_id: int):
    async with _db_pool.acquire() as conn:
        row = await get_produto(conn, produto_id)
        if not row:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        return dict(row)

@app.patch("/produtos/{produto_id}")
async def atualizar_produto(produto_id: int, payload: ProdutoUpdate):
    async with _db_pool.acquire() as conn:
        # se categoria_id fornecido, verificar existência
        if payload.categoria_id is not None:
            exists = await conn.fetchval("SELECT 1 FROM categoria WHERE id=$1", payload.categoria_id)
            if not exists:
                raise HTTPException(status_code=404, detail="Categoria não encontrada")
        try:
            async with conn.transaction():
                row = await update_produto_db(conn, produto_id, payload)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Produto com esse nome já existe nessa categoria")
        if not row:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
    return dict(row)

@app.delete("/produtos/{produto_id}", status_code=204)
async def deletar_produto(produto_id: int):
    async with _db_pool.acquire() as conn:
        async with conn.transaction():
            res = await conn.execute("DELETE FROM produto WHERE id=$1", produto_id)
            # res é algo como 'DELETE 1' ou 'DELETE 0'
            if res.endswith(" 0"):
                raise HTTPException(status_code=404, detail="Produto não encontrado")
    return

# ---- Execução local para desenvolvimento ----
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("products:app", host="127.0.0.1", port=8001, reload=True)
