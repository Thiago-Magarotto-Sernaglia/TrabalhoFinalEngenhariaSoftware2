import asyncpg
from fastapi import HTTPException
from passlib.hash import bcrypt

# Imports consolidados
from repositories import CategoriaRepository, ClienteRepository, ProdutoRepository, AdminRepository
from schemas import ProdutoIn, ProdutoUpdate

class ProdutoService:
    def __init__(self, db_pool: asyncpg.pool.Pool):
        self.pool = db_pool

    async def criar_produto(self, produto: ProdutoIn):
        async with self.pool.acquire() as conn:
            cat_repo = CategoriaRepository(conn)
            prod_repo = ProdutoRepository(conn)
            if produto.categoria_id is not None:
                if not await cat_repo.exists_by_id(produto.categoria_id):
                    raise HTTPException(status_code=404, detail="Categoria não encontrada")
            try:
                async with conn.transaction():
                    pid = await prod_repo.create(produto)
                    return {"id": pid}
            except asyncpg.UniqueViolationError as err:
                raise HTTPException(status_code=400, detail="Produto já cadastrado na mesma categoria") from err

    async def listar_produtos(self):
        async with self.pool.acquire() as conn:
            repo = ProdutoRepository(conn)
            return await repo.list_all()

    async def obter_produto(self, pid: int):
        async with self.pool.acquire() as conn:
            repo = ProdutoRepository(conn)
            row = await repo.get_by_id(pid)
            if not row: raise HTTPException(status_code=404, detail="Produto não encontrado")
            return dict(row)

    async def atualizar_produto(self, pid: int, dados: "ProdutoUpdate"):
        async with self.pool.acquire() as conn:
            repo = ProdutoRepository(conn)
            atualizado = await repo.update(pid, dados)
            if not atualizado: raise HTTPException(status_code=404, detail="Produto não encontrado")
            return dict(atualizado)

    async def deletar_produto(self, pid: int):
        async with self.pool.acquire() as conn:
            repo = ProdutoRepository(conn)
            if not await repo.delete(pid):
                raise HTTPException(status_code=404, detail="Produto não encontrado")
            return {"msg": "Produto removido com sucesso"}


class ClienteService:
    def __init__(self, db_pool: asyncpg.pool.Pool):
        self.pool = db_pool

    async def criar_cliente(self, nome: str, email: str, senha: str):
        async with self.pool.acquire() as conn:
            repo = ClienteRepository(conn)
            if await repo.get_by_email(email):
                raise HTTPException(status_code=400, detail="E-mail já cadastrado.")
            senha_hash = bcrypt.hash(senha)
            cliente_id = await repo.create(nome, email, senha_hash)
            return {"id": cliente_id, "msg": "Cliente criado com sucesso"}

    async def autenticar(self, email: str, senha: str):
        async with self.pool.acquire() as conn:
            repo = ClienteRepository(conn)
            user = await repo.get_by_email(email)
            if not user or not bcrypt.verify(senha, user["senha_hash"]):
                raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")
            return {"id": user["id"], "nome": user["nome"], "email": user["email"]}

class AdminService:
    def __init__(self, db_pool: asyncpg.pool.Pool):
        self.pool = db_pool

    async def criar_admin(self, nome: str, email: str, senha: str):
        async with self.pool.acquire() as conn:
            repo = AdminRepository(conn)
            if await repo.get_by_email(email):
                raise HTTPException(status_code=400, detail="E-mail de administrador já existe.")
            senha_hash = bcrypt.hash(senha)
            admin_id = await repo.create(nome, email, senha_hash)
            return {"id": admin_id, "msg": "Administrador criado com sucesso"}

    async def autenticar_admin(self, email: str, senha: str):
        async with self.pool.acquire() as conn:
            repo = AdminRepository(conn)
            admin = await repo.get_by_email(email)
            if not admin:
                raise HTTPException(status_code=401, detail="Credenciais inválidas")
            if not bcrypt.verify(senha, admin["senha_hash"]):
                raise HTTPException(status_code=401, detail="Credenciais inválidas")
            return {"id": admin["id"], "nome": admin["nome"], "email": admin["email"], "role": "admin"}

    async def listar_admins(self):
        async with self.pool.acquire() as conn:
            repo = AdminRepository(conn)
            return await repo.list_all()

    async def deletar_admin(self, admin_id: int):
        async with self.pool.acquire() as conn:
            repo = AdminRepository(conn)
            if not await repo.delete(admin_id):
                raise HTTPException(status_code=404, detail="Administrador não encontrado")
            return {"msg": "Administrador removido"}