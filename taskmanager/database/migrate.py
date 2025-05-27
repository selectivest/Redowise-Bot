"""Database migration script."""

import asyncio
import importlib
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from .connection import async_session

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")

async def get_current_version(session: AsyncSession) -> int:
    """Get the current database version."""
    try:
        result = await session.execute(text("SELECT version FROM alembic_version;"))
        version = result.scalar_one_or_none()
        return int(version) if version is not None else 0
    except Exception:
        # If the table does not exist, create it and return 0.
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS alembic_version (version INTEGER NOT NULL);
            INSERT INTO alembic_version (version) VALUES (0);
        """))
        await session.commit()
        return 0

async def set_version(session: AsyncSession, version: int) -> None:
    """Set the current database version."""
    await session.execute(text("UPDATE alembic_version SET version = :version;"), {"version": version})
    await session.commit()

async def run_migrations() -> None:
    """Run pending migrations (if any) in the migrations directory."""
    sys.path.insert(0, MIGRATIONS_DIR)
    async with async_session() as session:
        current_version = await get_current_version(session)
        migration_files = sorted([ f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".py") and not f.startswith("__") ])
        for (i, migration_file) in enumerate(migration_files, start=1):
            if (i > current_version):
                mod_name = os.path.splitext(migration_file)[0]
                mod = importlib.import_module(mod_name)
                print(f"Running migration: { mod_name } (up)...")
                await mod.upgrade(session.get_bind().sync_engine.connect())
                await set_version(session, i)
                print("Migration (up) completed.")
        sys.path.pop(0)

if __name__ == "__main__":
    asyncio.run(run_migrations()) 