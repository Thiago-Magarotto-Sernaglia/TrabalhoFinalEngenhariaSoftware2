from fastapi import FastAPI, Depends
from schemas import ProdutoIn, CategoriaIn
from database import db, init_db
from services import ProdutoService
# Importar os repositories se for fazer queries simples direto na rota (opcional)
from repositories import CategoriaRepository

app = FastAPI()

@app.on_event("startup")
async def startup():
    await db.connect()
    await init_db()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

# Dependency Injection simples para o Service
def get_produto_service():
    return ProdutoService(db.pool)

# ---- Rotas ----

@app.post("/produtos")
async def criar_produto(
    payload: ProdutoIn, 
    service: ProdutoService = Depends(get_produto_service)
):
    return await service.criar_produto(payload)

@app.get("/produtos")
async def listar_produtos(
    service: ProdutoService = Depends(get_produto_service)
):
    return await service.listar_produtos()

@app.get("/produtos/{id}")
async def obter_produto(
    id: int,
    service: ProdutoService = Depends(get_produto_service)
):
    return await service.obter_produto(id)

# Exemplo de uso direto do Repo para coisas muito simples (Categorias)
# Em sistemas grandes, recomenda-se criar CategoriaService também
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
        except Exception: # Simplificado
             from fastapi import HTTPException
             raise HTTPException(status_code=400, detail="Erro ao criar categoria")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)