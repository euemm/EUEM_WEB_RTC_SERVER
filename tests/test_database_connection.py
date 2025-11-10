import pytest

from src.utils.db import get_db_pool, close_db_pool


@pytest.mark.asyncio
async def test_database_connection_select_1():
    """Ensure the PostgreSQL pool can connect and execute a simple query."""
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        result = await connection.fetchval("SELECT 1")
        assert result == 1

    await close_db_pool()
