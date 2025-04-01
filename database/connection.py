from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

# Get the absolute path to the database file
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'taskmanager.db')

# Create async engine
engine = create_async_engine(
    f'sqlite+aiosqlite:///{db_path}',
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

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session 