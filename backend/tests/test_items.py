import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
import asyncpg
from items import app
import os

pytestmark = pytest.mark.asyncio

TEST_DB_URL = os.getenv("TEST_DB_URL", "postgresql://user:pass@db:5432/test_db")

@pytest_asyncio.fixture
async def db_connection():
    """Fixture para conexão com banco de testes"""
    try:
        conn = await asyncpg.connect(TEST_DB_URL)
        # Criar tabela de exemplo se não existir
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS exemplo (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL
            );
        """)
        tr = conn.transaction()
        await tr.start()
        yield conn
        await tr.rollback()
        await conn.close()
    except Exception as e:
        pytest.skip(f"Não foi possível conectar ao banco: {e}")

async def test_criar_item_sucesso(db_connection):
    """Testa criação de item com sucesso"""
    # Mock do get_conn para retornar nossa conexão de teste
    from items import get_conn
    app.dependency_overrides[get_conn] = lambda: db_connection
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/itens?nome=Item Teste")
    
    assert response.status_code == 200
    assert "id" in response.json()
    assert isinstance(response.json()["id"], int)
    
    app.dependency_overrides = {}

async def test_listar_itens(db_connection):
    """Testa listagem de itens"""
    # Primeiro cria alguns itens
    await db_connection.execute("INSERT INTO exemplo (nome) VALUES ('Item 1'), ('Item 2')")
    
    from items import get_conn
    app.dependency_overrides[get_conn] = lambda: db_connection
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/itens")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 2
    
    app.dependency_overrides = {}

async def test_obter_item_por_id_sucesso(db_connection):
    """Testa obter item por ID com sucesso"""
    # Cria um item primeiro
    row = await db_connection.fetchrow("INSERT INTO exemplo (nome) VALUES ($1) RETURNING id", "Item Teste")
    item_id = row["id"]
    
    from items import get_conn
    app.dependency_overrides[get_conn] = lambda: db_connection
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/itens/{item_id}")
    
    assert response.status_code == 200
    assert response.json()["id"] == item_id
    assert response.json()["nome"] == "Item Teste"
    
    app.dependency_overrides = {}

async def test_obter_item_por_id_nao_encontrado(db_connection):
    """Testa obter item por ID que não existe"""
    from items import get_conn
    app.dependency_overrides[get_conn] = lambda: db_connection
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/itens/99999")
    
    assert response.status_code == 404
    assert "não encontrado" in response.json()["detail"].lower()
    
    app.dependency_overrides = {}

