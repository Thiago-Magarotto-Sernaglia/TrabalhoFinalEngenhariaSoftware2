from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from main import app, get_produto_service

pytestmark = pytest.mark.asyncio


async def test_rota_criar_produto(mocker):

    mock_service = mocker.Mock()
    mock_service.criar_produto = AsyncMock(return_value={"id": 123})

    app.dependency_overrides[get_produto_service] = lambda: mock_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"nome": "Produto API", "preco": 50.0, "unidade": "cx", "categoria_id": 1}
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


async def test_rota_obter_produto_por_id(mocker):
    """Testa obter produto por ID"""
    mock_service = mocker.Mock()
    mock_service.obter_produto = AsyncMock(
        return_value={"id": 1, "nome": "Produto Teste", "preco": 10.0}
    )

    app.dependency_overrides[get_produto_service] = lambda: mock_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/produtos/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["nome"] == "Produto Teste"

    app.dependency_overrides = {}


async def test_rota_obter_produto_nao_encontrado(mocker):
    """Testa obter produto que não existe"""
    from fastapi import HTTPException

    mock_service = mocker.Mock()
    mock_service.obter_produto = AsyncMock(
        side_effect=HTTPException(status_code=404, detail="Produto não encontrado")
    )

    app.dependency_overrides[get_produto_service] = lambda: mock_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/produtos/999")

    assert response.status_code == 404

    app.dependency_overrides = {}


async def test_rota_listar_categorias(mocker):
    """Testa listagem de categorias"""
    from unittest.mock import AsyncMock, MagicMock

    # Mock da conexão e repositório
    mock_conn = MagicMock()
    mock_repo = MagicMock()
    mock_repo.list_all = AsyncMock(return_value=[{"id": 1, "nome": "Categoria 1"}])

    # Mock do pool.acquire()
    mock_pool = MagicMock()
    mock_acquire = AsyncMock()
    mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire

    # Mock do database.db.pool
    from database import db

    original_pool = db.pool
    db.pool = mock_pool

    # Mock do CategoriaRepository
    with mocker.patch("main.CategoriaRepository", return_value=mock_repo):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/categorias")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Restaura o pool original
    db.pool = original_pool


async def test_rota_criar_categoria(mocker):
    """Testa criação de categoria"""
    from unittest.mock import AsyncMock, MagicMock

    mock_conn = MagicMock()
    mock_repo = MagicMock()
    mock_repo.create = AsyncMock(return_value=123)

    mock_pool = MagicMock()
    mock_acquire = AsyncMock()
    mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire

    from database import db

    original_pool = db.pool
    db.pool = mock_pool

    with mocker.patch("main.CategoriaRepository", return_value=mock_repo):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/categorias", json={"nome": "Nova Categoria"})

    assert response.status_code == 200
    assert response.json()["id"] == 123

    db.pool = original_pool
