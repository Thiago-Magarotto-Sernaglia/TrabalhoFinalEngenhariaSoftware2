import asyncpg
from schemas import CategoriaIn, ProdutoIn, ProdutoUpdate

class CategoriaRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create(self, categoria: CategoriaIn) -> int:
        row = await self.conn.fetchrow(
            "INSERT INTO categoria (nome) VALUES ($1) RETURNING id",
            categoria.nome
        )
        return row["id"]

    async def list_all(self):
        rows = await self.conn.fetch("SELECT id, nome FROM categoria ORDER BY nome")
        return [dict(r) for r in rows]

    async def exists_by_id(self, cat_id: int) -> bool:
        return await self.conn.fetchval("SELECT 1 FROM categoria WHERE id=$1", cat_id)

class ProdutoRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create(self, p: ProdutoIn) -> int:
        row = await self.conn.fetchrow(
            "INSERT INTO produto (nome, preco, unidade, categoria_id, estoque) VALUES ($1, $2, $3, $4, $5) RETURNING id",
            p.nome, p.preco, p.unidade, p.categoria_id, p.estoque
        )
        return row["id"]

    async def list_all(self):
        rows = await self.conn.fetch("""
            SELECT p.id, p.nome, p.preco::text AS preco, p.unidade, p.estoque,
                   c.id AS categoria_id, c.nome AS categoria_nome
            FROM produto p
            LEFT JOIN categoria c ON p.categoria_id = c.id
            ORDER BY p.id
        """)
        return [dict(r) for r in rows]

    async def get_by_id(self, pid: int):
        return await self.conn.fetchrow("SELECT * FROM produto WHERE id=$1", pid)

    async def delete(self, pid: int) -> bool:
        res = await self.conn.execute("DELETE FROM produto WHERE id=$1", pid)
        return not res.endswith(" 0") # Retorna True se deletou algo

    async def update(self, pid: int, u: ProdutoUpdate):
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
            return await self.get_by_id(pid)

        sql = "UPDATE produto SET " + ", ".join(cols) + f" WHERE id = ${idx} RETURNING *"
        vals.append(pid)
        return await self.conn.fetchrow(sql, *vals)