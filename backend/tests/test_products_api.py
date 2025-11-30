import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import sys
import os
import asyncpg

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.login import app

client = TestClient(app)

@pytest.fixture
def override_db_pool():
    with patch('products._db_pool', new_callable=AsyncMock) as mock_pool:
        # Configura acquire (já tinhamos feito)
        mock_pool.acquire = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        # --- CORREÇÃO NOVA AQUI ---
        # Configura transaction para funcionar com 'async with'
        mock_conn.transaction = MagicMock()
        mock_transaction = AsyncMock()
        mock_conn.transaction.return_value.__aenter__.return_value = mock_transaction
        
        yield mock_conn

def test_listar_produtos_retorna_lista_vazia(override_db_pool):
    conn_mock = override_db_pool
    conn_mock.fetch.return_value = []
    response = client.get("/produtos")
    assert response.status_code == 200
    assert response.json() == []

def test_obter_produto_existente(override_db_pool):
    conn_mock = override_db_pool
    produto_id = 1
    produto_mock = {
        "id": produto_id, 
        "nome": "Banana", 
        "preco": "4.50",
        "unidade": "kg",
        "categoria_id": 1,
        "estoque": 10
    }
    conn_mock.fetchrow.return_value = produto_mock
    response = client.get(f"/produtos/{produto_id}")
    assert response.status_code == 200
    assert response.json() == produto_mock

def test_obter_produto_inexistente(override_db_pool):
    conn_mock = override_db_pool
    conn_mock.fetchrow.return_value = None
    response = client.get("/produtos/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Produto não encontrado"}

def test_criar_produto_sucesso(override_db_pool):
    conn_mock = override_db_pool
    conn_mock.fetchval.return_value = 1
    conn_mock.fetchrow.return_value = {"id": 100}
    novo_produto = {
        "nome": "Abacaxi",
        "preco": 6.00,
        "unidade": "un",
        "categoria_id": 1,
        "estoque": 20
    }
    response = client.post("/produtos", json=novo_produto)
    assert response.status_code == 200
    assert response.json() == {"id": 100}

def test_criar_produto_categoria_inexistente(override_db_pool):
    conn_mock = override_db_pool
    conn_mock.fetchval.return_value = None
    novo_produto = {
        "nome": "Produto Fantasma",
        "preco": 10.00,
        "unidade": "un",
        "categoria_id": 999
    }
    response = client.post("/produtos", json=novo_produto)
    assert response.status_code == 404
    assert response.json() == {"detail": "Categoria não encontrada"}

def test_criar_produto_duplicado(override_db_pool):
    conn_mock = override_db_pool
    conn_mock.fetchval.return_value = 1
    conn_mock.fetchrow.side_effect = asyncpg.UniqueViolationError()
    novo_produto = {
        "nome": "Banana",
        "preco": 4.50,
        "unidade": "kg",
        "categoria_id": 1
    }
    response = client.post("/produtos", json=novo_produto)
    assert response.status_code == 400
    assert response.json() == {"detail": "Produto já cadastrado na mesma categoria"}

def test_deletar_produto_sucesso(override_db_pool):
    conn_mock = override_db_pool
    conn_mock.execute.return_value = "DELETE 1"
    response = client.delete("/produtos/1")
    assert response.status_code == 204

def test_deletar_produto_inexistente(override_db_pool):
    conn_mock = override_db_pool
    conn_mock.execute.return_value = "DELETE 0"
    response = client.delete("/produtos/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Produto não encontrado"}