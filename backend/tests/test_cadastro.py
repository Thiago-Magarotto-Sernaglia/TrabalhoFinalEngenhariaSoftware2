from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from cadastro import app

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_redis():
    """Mock do Redis para os testes"""
    with patch("cadastro.r") as mock_r:
        yield mock_r


async def test_register_sucesso(mock_redis):
    """Testa registro de novo usuário com sucesso"""
    mock_redis.exists.return_value = False  # Usuário não existe
    mock_redis.set = AsyncMock()

    # Mock do bcrypt.hash para evitar problemas na inicialização
    with patch("cadastro.bcrypt.hash", return_value="$2b$12$hashed_password"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            payload = {"username": "testuser", "password": "senha123", "role": "user"}
            response = await ac.post("/register", json=payload)

    assert response.status_code == 201
    assert response.json()["msg"] == "usuário criado"
    assert response.json()["username"] == "testuser"
    mock_redis.set.assert_called_once()


async def test_register_usuario_existente(mock_redis):
    """Testa registro de usuário que já existe"""
    mock_redis.exists.return_value = True  # Usuário já existe

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"username": "testuser", "password": "senha123"}
        response = await ac.post("/register", json=payload)

    assert response.status_code == 400
    assert "já existe" in response.json()["detail"].lower()


async def test_register_username_invalido(mock_redis):
    """Testa registro com username muito curto"""
    mock_redis.exists.return_value = False

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"username": "ab", "password": "senha123"}  # Muito curto (min_length=3)
        response = await ac.post("/register", json=payload)

    assert response.status_code == 422  # Validação do Pydantic


async def test_register_senha_curta(mock_redis):
    """Testa registro com senha muito curta"""
    mock_redis.exists.return_value = False

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"username": "testuser", "password": "12345"}  # Muito curta (min_length=6)
        response = await ac.post("/register", json=payload)

    assert response.status_code == 422  # Validação do Pydantic
