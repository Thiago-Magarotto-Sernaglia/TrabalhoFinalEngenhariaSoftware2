"""
Script para inicializar o banco de dados de testes.
Executa as mesmas operações de init_db() mas pode ser chamado diretamente.
"""
import asyncio
import os
import asyncpg

DATABASE_URL = os.getenv("DATABASE_URL", os.getenv("TEST_DB_URL", "postgres://user:pass@localhost:5432/db"))

async def init_test_database():
    """Inicializa o banco de dados criando as tabelas necessárias."""
    print(f"Conectando ao banco: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Criar tabelas
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS categoria (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL UNIQUE
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS produto (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                preco NUMERIC NOT NULL,
                unidade TEXT NOT NULL,
                categoria_id INTEGER REFERENCES categoria(id),
                estoque INTEGER NOT NULL DEFAULT 0,
                UNIQUE(nome, categoria_id)
            );
        """)
        
        # Seeds iniciais (apenas se não existirem)
        await conn.execute("""
            INSERT INTO categoria (nome)
            SELECT v FROM (VALUES ('frutas'), ('verduras'), ('hortifruti')) AS t(v)
            ON CONFLICT (nome) DO NOTHING;
        """)
        
        print("Banco de dados inicializado com sucesso!")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(init_test_database())

