import asyncio
from typing import AsyncIterator, Iterator

import asyncpg
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.utils.config import reload_settings, get_settings
from src.auth.jwt_handler import pwd_context
from src.utils import db as db_module


async def _seed_users() -> None:
    settings = get_settings()
    conn = await asyncpg.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
    )
    try:
        await conn.execute("INSERT INTO roles(name) VALUES('USER') ON CONFLICT (name) DO NOTHING")
        await conn.execute("INSERT INTO roles(name) VALUES('ADMIN') ON CONFLICT (name) DO NOTHING")

        async def upsert_user(email: str, password: str, first_name: str, last_name: str) -> str:
            hashed_password = pwd_context.hash(password)
            row = await conn.fetchrow(
                """
                INSERT INTO users (email, password, first_name, last_name, is_verified, is_enabled)
                VALUES ($1, $2, $3, $4, TRUE, TRUE)
                ON CONFLICT (email) DO UPDATE SET
                    password = EXCLUDED.password,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    is_verified = TRUE,
                    is_enabled = TRUE,
                    updated_at = now()
                RETURNING id
                """,
                email,
                hashed_password,
                first_name,
                last_name,
            )
            return str(row["id"])

        admin_id = await upsert_user("admin", "admin123", "Admin", "User")
        user1_id = await upsert_user("user1", "password123", "User", "One")

        role_rows = await conn.fetch("SELECT id, name FROM roles WHERE name = ANY($1)", ["USER", "ADMIN"])
        role_map = {row["name"]: row["id"] for row in role_rows}

        await conn.execute(
            "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            admin_id,
            role_map.get("ADMIN") or role_map.get("USER"),
        )
        await conn.execute(
            "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            admin_id,
            role_map["USER"],
        )
        await conn.execute(
            "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            user1_id,
            role_map["USER"],
        )
    finally:
        await conn.close()


@pytest.fixture(scope="session", autouse=True)
def seed_test_data() -> None:
    reload_settings()
    asyncio.run(_seed_users())


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
    asyncio.run(db_module.close_db_pool())
