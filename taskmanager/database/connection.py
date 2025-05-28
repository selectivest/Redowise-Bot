from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from typing import AsyncGenerator

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///taskmanager.db')

# Create async engine
engine = create_async_engine(
    DATABASE_URL.replace('sqlite:///', 'sqlite+aiosqlite:///'),
    echo=True,
    future=True,
    connect_args={"check_same_thread": False}  # Allow multiple threads to access the database
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,  # Ensure transactions are explicit
    autoflush=False  # Ensure flushes are explicit
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session 