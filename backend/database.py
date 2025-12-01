import os

import asyncpg

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgres://user:pass@localhost:5432/db"
)  # Fallback para dev


class Database:
    def __init__(self):
        self.pool: asyncpg.pool.Pool | None = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
            print("Conexão com o banco estabelecida.")

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            print("Conexão com o banco encerrada.")

    async def get_connection(self):
        # Helper para usar em contextos manuais se necessário
        if not self.pool:
            await self.connect()
        return self.pool.acquire()


# Instância global para ser importada
db = Database()


# Função para criar tabelas iniciais (migração simplificada)
async def init_db():
    async with db.pool.acquire() as conn:
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

        # Seeds iniciais
        await conn.execute(
            """
            INSERT INTO categoria (nome)
            SELECT v FROM (VALUES ('frutas'), ('verduras'), ('hortifruti')) AS t(v)
            ON CONFLICT (nome) DO NOTHING;
        """
        )
