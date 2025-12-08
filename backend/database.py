import asyncio
import os

import asyncpg

DATABASE_URL = os.getenv("DATABASE_URL", "postgres://user:pass@localhost:5432/db")


class Database:
    def __init__(self):
        self.pool: asyncpg.pool.Pool | None = None

    async def connect(self):
        if not self.pool:
            max_retries = 5
            for attempt in range(1, max_retries + 1):
                try:
                    print(f"Tentando conectar ao banco (Tentativa {attempt}/{max_retries})...")
                    self.pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
                    print("✅ Conexão com o banco estabelecida com sucesso.")
                    return
                except (OSError, asyncpg.CannotConnectNowError, ConnectionRefusedError) as e:
                    if attempt == max_retries:
                        print(
                            f"❌ Falha crítica: Não foi possível conectar ao banco após {max_retries} tentativas."
                        )
                        raise e
                    print("⚠️ Banco ainda não está pronto. Aguardando 3 segundos...")
                    await asyncio.sleep(3)

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            print("Conexão com o banco encerrada.")

    async def get_connection(self):
        if not self.pool:
            await self.connect()
        return self.pool.acquire()


# Instância global
db = Database()


async def init_db():
    """
    Executa os comandos SQL um a um, tratando erros de concorrência.
    Isso evita que múltiplos workers quebrem ao tentar criar a mesma tabela simultaneamente.
    """
    commands = [
        # 1. Tabela Categoria
        """
        CREATE TABLE IF NOT EXISTS categoria (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE
        );
        """,
        # 2. Tabela Produto
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
        """,
        # 3. Tabela Cliente
        """
        CREATE TABLE IF NOT EXISTS cliente (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL
        );
        """,
        # 4. Seeds (Categorias)
        """
        INSERT INTO categoria (nome)
        VALUES 
            ('Eletrônicos'), 
            ('Acessórios'), 
            ('Computadores'), 
            ('Smartphones'), 
            ('Games')
        ON CONFLICT (nome) DO NOTHING;
        """,
    ]

    async with db.pool.acquire() as conn:
        for sql in commands:
            try:
                await conn.execute(sql)
            except (asyncpg.UniqueViolationError, asyncpg.DuplicateTableError):
                # Se der erro de duplicidade, significa que outro worker foi mais rápido
                # e já criou a tabela/dado. Podemos ignorar e seguir em frente.
                pass
            except Exception as e:
                print(f"Erro ao executar SQL de inicialização: {e}")
                # Não relançamos o erro para não derrubar o container,
                # mas logamos para debug.
