import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from login import app

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_redis():
    """Mock do Redis para os testes"""
    with patch("login.r") as mock_r:
        yield mock_r


async def test_login_sucesso(mock_redis):
    """Testa login com credenciais válidas"""
    # Mock do usuário no Redis
    user_data = {"id": 1, "username": "alice", "password": "senha123", "role": "admin"}
    mock_redis.get.return_value = json.dumps(user_data)
    mock_redis.set = AsyncMock()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"username": "alice", "password": "senha123"}
        response = await ac.post("/login", json=payload)

    assert response.status_code == 200
    assert response.json()["msg"] == "logado"
    # Verifica se cookie foi setado
    assert "session_id" in response.cookies


async def test_login_credenciais_invalidas_usuario_inexistente(mock_redis):
    """Testa login com usuário que não existe"""
    mock_redis.get.return_value = None

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"username": "inexistente", "password": "senha123"}
        response = await ac.post("/login", json=payload)

    assert response.status_code == 401
    assert "inválidas" in response.json()["detail"].lower()


async def test_login_senha_incorreta(mock_redis):
    """Testa login com senha incorreta"""
    user_data = {"id": 1, "username": "alice", "password": "senha123", "role": "admin"}
    mock_redis.get.return_value = json.dumps(user_data)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"username": "alice", "password": "senha_errada"}
        response = await ac.post("/login", json=payload)

    assert response.status_code == 401
    assert "inválidas" in response.json()["detail"].lower()


async def test_logout_sucesso(mock_redis):
    """Testa logout com sucesso"""
    mock_redis.delete = AsyncMock()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Primeiro faz login para ter cookie
        user_data = {"id": 1, "username": "alice", "password": "senha123", "role": "admin"}
        mock_redis.get.return_value = json.dumps(user_data)
        mock_redis.set = AsyncMock()

        login_response = await ac.post("/login", json={"username": "alice", "password": "senha123"})
        session_id = login_response.cookies.get("session_id")

        # Agora faz logout
        mock_redis.get.return_value = json.dumps(
            {"user_id": 1, "username": "alice", "role": "admin"}
        )
        response = await ac.post("/logout", cookies={"session_id": session_id})

    assert response.status_code == 200
    assert response.json()["msg"] == "deslogado"


async def test_profile_nao_autenticado():
    """Testa acesso ao profile sem autenticação"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/profile")

    assert response.status_code == 401


async def test_admin_sem_permissao(mock_redis):
    """Testa acesso à área admin sem ser admin"""
    session_data = {"user_id": 2, "username": "bob", "role": "user"}
    mock_redis.get.return_value = json.dumps(session_data)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/admin", cookies={"session_id": "fake_session"})

    assert response.status_code == 403


async def test_admin_com_permissao(mock_redis):
    """Testa acesso à área admin sendo admin"""
    session_data = {"user_id": 1, "username": "alice", "role": "admin"}
    mock_redis.get.return_value = json.dumps(session_data)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/admin", cookies={"session_id": "fake_session"})

    assert response.status_code == 200
    assert "admin" in response.json()["msg"].lower()
