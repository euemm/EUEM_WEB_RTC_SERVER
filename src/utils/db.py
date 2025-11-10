from __future__ import annotations

import asyncio
import logging
from typing import Dict

import asyncpg  # type: ignore

from .config import get_settings

logger = logging.getLogger(__name__)

_pools: Dict[int, asyncpg.Pool] = {}
_locks: Dict[int, asyncio.Lock] = {}


async def get_db_pool() -> asyncpg.Pool:
    """Return a shared asyncpg connection pool for the current event loop."""
    loop = asyncio.get_running_loop()
    loop_id = id(loop)

    pool = _pools.get(loop_id)
    if pool is not None:
        return pool

    lock = _locks.get(loop_id)
    if lock is None:
        lock = asyncio.Lock()
        _locks[loop_id] = lock

    async with lock:
        pool = _pools.get(loop_id)
        if pool is not None:
            return pool

        settings = get_settings()
        logger.info(
            "Initializing PostgreSQL pool",
            extra={
                "host": settings.db_host,
                "port": settings.db_port,
                "database": settings.db_name,
            },
        )
        pool = await asyncpg.create_pool(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
            min_size=settings.db_pool_min_size,
            max_size=settings.db_pool_max_size,
        )
        _pools[loop_id] = pool
        return pool


async def close_db_pool() -> None:
    """Close the asyncpg pool bound to the current event loop."""
    loop = asyncio.get_running_loop()
    loop_id = id(loop)
    pool = _pools.pop(loop_id, None)
    if pool is not None:
        await pool.close()
        logger.info("PostgreSQL pool closed")
    _locks.pop(loop_id, None)
