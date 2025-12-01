import sys
import os
import pytest
from unittest.mock import MagicMock, AsyncMock


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_db_pool():
    """
    Simula o pool de conexões do asyncpg e suas transações.
    """
    pool = MagicMock()
    connection = AsyncMock()
    
    # --- Configura pool.acquire() ---
   
    acquirer = AsyncMock()
    acquirer.__aenter__.return_value = connection
    acquirer.__aexit__.return_value = None
    
    # Quando chamamos pool.acquire(), retorna esse gerenciador imediatamente
    pool.acquire.return_value = acquirer

    # --- Configura conn.transaction() ---
    # conn.transaction() é um método SÍNCRONO que retorna um Async Context Manager.
    transaction_ctx = AsyncMock()
    transaction_ctx.__aenter__.return_value = None
    transaction_ctx.__aexit__.return_value = None
    
    
    connection.transaction = MagicMock(return_value=transaction_ctx)

    return pool, connection