import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock
from main import app, get_produto_service


pytestmark = pytest.mark.asyncio

async def test_rota_criar_produto(mocker):
  
    mock_service = mocker.Mock()
    mock_service.criar_produto = AsyncMock(return_value={"id": 123})


    app.dependency_overrides[get_produto_service] = lambda: mock_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "nome": "Produto API",
            "preco": 50.0,
            "unidade": "cx",
            "categoria_id": 1
        }
        response = await ac.post("/produtos", json=payload)

 
    assert response.status_code == 200
    assert response.json() == {"id": 123}
    
    # Limpa overrides
    app.dependency_overrides = {}

async def test_rota_listar_produtos(mocker):
    mock_service = mocker.Mock()
    # Simula retorno de lista vazia
    mock_service.listar_produtos = AsyncMock(return_value=[])

    app.dependency_overrides[get_produto_service] = lambda: mock_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/produtos")

    assert response.status_code == 200
    assert response.json() == []
    
    app.dependency_overrides = {}