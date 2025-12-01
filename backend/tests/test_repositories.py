import pytest
import asyncpg
import os
from repositories import CategoriaRepository
from schemas import CategoriaIn
import pytest_asyncio


TEST_DB_URL = os.getenv("TEST_DB_URL", "postgresql://user:pass@db:5432/test_db")

@pytest_asyncio.fixture
async def db_connection():
    try:
        
        conn = await asyncpg.connect(TEST_DB_URL)
    except OSError as e:
        pytest.fail(f"Falha ao conectar no banco de testes ({TEST_DB_URL}). Verifique se o serviço está rodando e o host está correto. Erro: {e}")

    
    tr = conn.transaction()
    await tr.start()
    
    yield conn
    
    await tr.rollback() 
    await conn.close()

@pytest.mark.asyncio
async def test_categoria_repository_create(db_connection):
    repo = CategoriaRepository(db_connection)
    
    nova_cat = CategoriaIn(nome="Integration Test Cat")
    cat_id = await repo.create(nova_cat)
    
    assert isinstance(cat_id, int)
    

    salvo = await repo.exists_by_id(cat_id)
    assert salvo 