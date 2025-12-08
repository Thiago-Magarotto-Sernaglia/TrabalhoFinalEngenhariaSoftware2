from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, init_db
from repositories import CategoriaRepository
from schemas import CategoriaIn, ProdutoIn
from services import ProdutoService, ClienteService 
from schemas import ProdutoUpdate

app = FastAPI()

# ==================================================================
# CONFIGURAÇÃO DE CORS
# ==================================================================
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await db.connect()
    await init_db()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

# ==================================================================
# INJEÇÃO DE DEPENDÊNCIAS
# ==================================================================
def get_produto_service():
    return ProdutoService(db.pool)

def get_cliente_service():
    return ClienteService(db.pool)

# ==================================================================
# MODELOS PYDANTIC (Para requisições que não estão no schemas.py)
# ==================================================================
class ClienteCadastro(BaseModel):
    nome: str
    email: str
    senha: str

class LoginDados(BaseModel):
    email: str
    password: str

# ==================================================================
# ROTAS - PRODUTOS E CATEGORIAS
# ==================================================================
@app.post("/produtos")
async def criar_produto(payload: ProdutoIn, service: ProdutoService = Depends(get_produto_service)):
    return await service.criar_produto(payload)

@app.get("/produtos")
async def listar_produtos(service: ProdutoService = Depends(get_produto_service)):
    return await service.listar_produtos()

@app.get("/produtos/{id}")
async def obter_produto(id: int, service: ProdutoService = Depends(get_produto_service)):
    prod = await service.obter_produto(id)
    if not prod:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return prod

@app.put("/produtos/{id}")
async def atualizar_produto(id: int, payload: ProdutoUpdate, service: ProdutoService = Depends(get_produto_service)):
    return await service.atualizar_produto(id, payload)

@app.delete("/produtos/{id}")
async def deletar_produto(id: int, service: ProdutoService = Depends(get_produto_service)):
    return await service.deletar_produto(id)

@app.get("/categorias")
async def listar_categorias():
    async with db.pool.acquire() as conn:
        repo = CategoriaRepository(conn)
        return await repo.list_all()

@app.post("/categorias")
async def criar_categoria(payload: CategoriaIn):
    async with db.pool.acquire() as conn:
        repo = CategoriaRepository(conn)
        try:
            cid = await repo.create(payload)
            return {"id": cid}
        except Exception as err:
            raise HTTPException(status_code=400, detail="Erro ao criar categoria") from err

@app.get("/dashboard/stats")
async def get_dashboard_stats():
    """
    Retorna estatísticas gerais para o painel administrativo.
    """
    async with db.pool.acquire() as conn:
        # 1. Total de Produtos
        total_produtos = await conn.fetchval("SELECT COUNT(*) FROM produto")
        
        # 2. Produtos com Estoque Baixo (ex: menos de 10 unidades)
        estoque_baixo = await conn.fetchval("SELECT COUNT(*) FROM produto WHERE estoque < 10")
        
        # 3. Valor Total do Inventário (Soma de preço * estoque)
        # O COALESCE garante que retorne 0 se a tabela estiver vazia
        valor_inventario = await conn.fetchval("SELECT COALESCE(SUM(preco * estoque), 0) FROM produto")
        
        # 4. Total de Clientes (Já que criamos a tabela)
        total_clientes = await conn.fetchval("SELECT COUNT(*) FROM cliente")

        return {
            "total_produtos": total_produtos,
            "estoque_baixo": estoque_baixo,
            "valor_inventario": valor_inventario,
            "total_clientes": total_clientes
        }

# ==================================================================
# ROTAS - CLIENTES E LOGIN (Agora usando o Service Real)
# ==================================================================
@app.post("/clientes")
async def cadastrar_cliente(
    cliente: ClienteCadastro, 
    service: ClienteService = Depends(get_cliente_service)
):
    # O service já faz o hash da senha e verifica duplicidade
    return await service.criar_cliente(cliente.nome, cliente.email, cliente.senha)

@app.post("/login")
async def login_usuario(
    dados: LoginDados, 
    service: ClienteService = Depends(get_cliente_service)
):
    # O service verifica senha e retorna dados do usuário
    user = await service.autenticar(dados.email, dados.password)
    return {"msg": "Login realizado", "usuario": user}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)