import pytest
from fastapi import HTTPException
from services import ProdutoService
from schemas import ProdutoIn


pytestmark = pytest.mark.asyncio

async def test_criar_produto_sucesso(mock_db_pool):
    pool_mock, conn_mock = mock_db_pool
    service = ProdutoService(pool_mock)
    
    payload = ProdutoIn(nome="Teste", preco=10.0, unidade="un", categoria_id=1)

    # Mock: Categoria existe 
    conn_mock.fetchval.return_value = True 
    # Mock: Produto criado 
    conn_mock.fetchrow.return_value = {"id": 50}

    # Executa
    resultado = await service.criar_produto(payload)

    # Valida
    assert resultado == {"id": 50}
    # Garante que usou transação
    conn_mock.transaction.assert_called_once()

async def test_criar_produto_sem_categoria(mock_db_pool):
    pool_mock, conn_mock = mock_db_pool
    service = ProdutoService(pool_mock)
    
    # Tenta criar com categoria inexistente
    payload = ProdutoIn(nome="Teste", preco=10.0, unidade="un", categoria_id=999)

    # Mock: Categoria NÃO existe
    conn_mock.fetchval.return_value = None 

    # Valida se lança erro 404
    with pytest.raises(HTTPException) as exc:
        await service.criar_produto(payload)
    
    assert exc.value.status_code == 404
    assert exc.value.detail == "Categoria não encontrada"