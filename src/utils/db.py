from __future__ import annotations

import asyncio
import logging
from typing import Optional

import asyncpg

from .config import get_settings

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None
_pool_lock = asyncio.Lock()


async def get_db_pool() -> asyncpg.Pool:
    """Return a shared asyncpg connection pool."""
    global _pool

    if _pool is not None:
        return _pool

    async with _pool_lock:
        if _pool is not None:
            return _pool

        settings = get_settings()
        logger.info(
            "Initializing PostgreSQL pool", extra={
                "host": settings.db_host,
                "port": settings.db_port,
                "database": settings.db_name,
            }
        )
        _pool = await asyncpg.create_pool(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
            min_size=settings.db_pool_min_size,
            max_size=settings.db_pool_max_size,
        )
        return _pool


async def close_db_pool() -> None:
    """Gracefully close the shared connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("PostgreSQL pool closed")
