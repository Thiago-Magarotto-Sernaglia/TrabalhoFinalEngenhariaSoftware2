import os

import asyncpg
import pytest
import pytest_asyncio

from repositories import CategoriaRepository, ProdutoRepository
from schemas import CategoriaIn, ProdutoIn, ProdutoUpdate

TEST_DB_URL = os.getenv("TEST_DB_URL", "postgresql://user:pass@db:5432/test_db")


@pytest_asyncio.fixture
async def db_connection():
    try:
        conn = await asyncpg.connect(TEST_DB_URL)
        # Garantir que as tabelas existem
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS categoria (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL UNIQUE
            );
        """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS produto (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                preco NUMERIC NOT NULL,
                unidade TEXT NOT NULL,
                categoria_id INTEGER REFERENCES categoria(id),
                estoque INTEGER NOT NULL DEFAULT 0,
                UNIQUE(nome, categoria_id)
            );
        """
        )
    except OSError as e:
        pytest.fail(
            f"Falha ao conectar no banco de testes ({TEST_DB_URL}). Verifique se o serviço está rodando e o host está correto. Erro: {e}"
        )

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


@pytest.mark.asyncio
async def test_categoria_repository_list_all(db_connection):
    """Testa listagem de todas as categorias"""
    repo = CategoriaRepository(db_connection)

    # Cria algumas categorias
    await repo.create(CategoriaIn(nome="Categoria A"))
    await repo.create(CategoriaIn(nome="Categoria B"))

    categorias = await repo.list_all()

    assert isinstance(categorias, list)
    assert len(categorias) >= 2
    assert all("id" in cat and "nome" in cat for cat in categorias)


@pytest.mark.asyncio
async def test_categoria_repository_exists_by_id(db_connection):
    """Testa verificação de existência de categoria por ID"""
    repo = CategoriaRepository(db_connection)

    cat_id = await repo.create(CategoriaIn(nome="Test Exists"))

    # exists_by_id retorna 1 (truthy) quando encontra, None (falsy) quando não encontra
    assert await repo.exists_by_id(cat_id)  # Verifica se é truthy
    assert not await repo.exists_by_id(99999)  # Verifica se é falsy


@pytest.mark.asyncio
async def test_produto_repository_create(db_connection):
    """Testa criação de produto"""
    cat_repo = CategoriaRepository(db_connection)
    prod_repo = ProdutoRepository(db_connection)

    # Cria categoria primeiro
    cat_id = await cat_repo.create(CategoriaIn(nome="Categoria Produto"))

    produto = ProdutoIn(
        nome="Produto Teste", preco=10.0, unidade="un", categoria_id=cat_id, estoque=5
    )
    prod_id = await prod_repo.create(produto)

    assert isinstance(prod_id, int)


@pytest.mark.asyncio
async def test_produto_repository_list_all(db_connection):
    """Testa listagem de todos os produtos"""
    cat_repo = CategoriaRepository(db_connection)
    prod_repo = ProdutoRepository(db_connection)

    cat_id = await cat_repo.create(CategoriaIn(nome="Cat List"))
    await prod_repo.create(
        ProdutoIn(nome="Produto 1", preco=10.0, unidade="un", categoria_id=cat_id)
    )
    await prod_repo.create(
        ProdutoIn(nome="Produto 2", preco=20.0, unidade="un", categoria_id=cat_id)
    )

    produtos = await prod_repo.list_all()

    assert isinstance(produtos, list)
    assert len(produtos) >= 2


@pytest.mark.asyncio
async def test_produto_repository_get_by_id(db_connection):
    """Testa obter produto por ID"""
    cat_repo = CategoriaRepository(db_connection)
    prod_repo = ProdutoRepository(db_connection)

    cat_id = await cat_repo.create(CategoriaIn(nome="Cat Get"))
    prod_id = await prod_repo.create(
        ProdutoIn(nome="Produto Get", preco=15.0, unidade="un", categoria_id=cat_id)
    )

    produto = await prod_repo.get_by_id(prod_id)

    assert produto is not None
    assert produto["id"] == prod_id
    assert produto["nome"] == "Produto Get"


@pytest.mark.asyncio
async def test_produto_repository_delete(db_connection):
    """Testa deleção de produto"""
    cat_repo = CategoriaRepository(db_connection)
    prod_repo = ProdutoRepository(db_connection)

    cat_id = await cat_repo.create(CategoriaIn(nome="Cat Delete"))
    prod_id = await prod_repo.create(
        ProdutoIn(nome="Produto Delete", preco=10.0, unidade="un", categoria_id=cat_id)
    )

    deletado = await prod_repo.delete(prod_id)
    assert deletado is True

    # Tenta deletar novamente (não deve encontrar)
    deletado_novamente = await prod_repo.delete(prod_id)
    assert deletado_novamente is False


@pytest.mark.asyncio
async def test_produto_repository_update(db_connection):
    """Testa atualização de produto"""
    cat_repo = CategoriaRepository(db_connection)
    prod_repo = ProdutoRepository(db_connection)

    cat_id = await cat_repo.create(CategoriaIn(nome="Cat Update"))
    prod_id = await prod_repo.create(
        ProdutoIn(nome="Produto Original", preco=10.0, unidade="un", categoria_id=cat_id, estoque=5)
    )

    update = ProdutoUpdate(nome="Produto Atualizado", preco=20.0)
    produto_atualizado = await prod_repo.update(prod_id, update)

    assert produto_atualizado["nome"] == "Produto Atualizado"
    assert float(produto_atualizado["preco"]) == 20.0
