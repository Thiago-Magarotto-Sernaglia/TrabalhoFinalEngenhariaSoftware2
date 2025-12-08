import asyncpg
from fastapi import HTTPException
from passlib.hash import bcrypt

from repositories import CategoriaRepository, ClienteRepository, ProdutoRepository
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

    async def atualizar_produto(self, pid: int, dados: "ProdutoUpdate"):
        async with self.pool.acquire() as conn:
            repo = ProdutoRepository(conn)
            # O repositório retorna a linha atualizada ou None se não achar
            atualizado = await repo.update(pid, dados)

            if not atualizado:
                raise HTTPException(status_code=404, detail="Produto não encontrado")

            return dict(atualizado)

    async def deletar_produto(self, pid: int):
        async with self.pool.acquire() as conn:
            repo = ProdutoRepository(conn)
            sucesso = await repo.delete(pid)

            if not sucesso:
                raise HTTPException(status_code=404, detail="Produto não encontrado")

            return {"msg": "Produto removido com sucesso"}


class ClienteService:
    def __init__(self, db_pool: asyncpg.pool.Pool):
        self.pool = db_pool

    async def criar_cliente(self, nome: str, email: str, senha: str):
        async with self.pool.acquire() as conn:
            repo = ClienteRepository(conn)

            # Verifica se já existe
            if await repo.get_by_email(email):
                raise HTTPException(status_code=400, detail="E-mail já cadastrado.")

            # Hash da senha
            senha_hash = bcrypt.hash(senha)

            # Salva
            cliente_id = await repo.create(nome, email, senha_hash)
            return {"id": cliente_id, "msg": "Cliente criado com sucesso"}

    async def autenticar(self, email: str, senha: str):
        async with self.pool.acquire() as conn:
            repo = ClienteRepository(conn)
            user = await repo.get_by_email(email)

            if not user:
                raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")

            if not bcrypt.verify(senha, user["senha_hash"]):
                raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")

            return {"id": user["id"], "nome": user["nome"], "email": user["email"]}

    # ... Métodos de update e delete seguiriam a mesma lógica ...
