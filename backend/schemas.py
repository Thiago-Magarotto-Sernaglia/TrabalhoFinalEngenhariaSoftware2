from pydantic import BaseModel

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