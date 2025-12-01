import asyncpg
from fastapi import HTTPException

from repositories import CategoriaRepository, ProdutoRepository
from schemas import ProdutoIn


class ProdutoService:
    def __init__(self, db_pool: asyncpg.pool.Pool):
        self.pool = db_pool

    async def criar_produto(self, produto: ProdutoIn):
        async with self.pool.acquire() as conn:
            # Instancia repositórios com a conexão atual
            cat_repo = CategoriaRepository(conn)
            prod_repo = ProdutoRepository(conn)

            # Regra de Negócio: Verificar se categoria existe
            if produto.categoria_id is not None:
                if not await cat_repo.exists_by_id(produto.categoria_id):
                    raise HTTPException(status_code=404, detail="Categoria não encontrada")

            try:
                # Transação para garantir integridade
                async with conn.transaction():
                    pid = await prod_repo.create(produto)
                    return {"id": pid}
            except asyncpg.UniqueViolationError as err:
                raise HTTPException(
                    status_code=400, detail="Produto já cadastrado na mesma categoria"
                ) from err

    async def listar_produtos(self):
        async with self.pool.acquire() as conn:
            repo = ProdutoRepository(conn)
            return await repo.list_all()

    async def obter_produto(self, pid: int):
        async with self.pool.acquire() as conn:
            repo = ProdutoRepository(conn)
            row = await repo.get_by_id(pid)
            if not row:
                raise HTTPException(status_code=404, detail="Produto não encontrado")
            return dict(row)

    # ... Métodos de update e delete seguiriam a mesma lógica ...
