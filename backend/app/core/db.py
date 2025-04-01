from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import MetaData

from app.core.config import settings

# SQLAlchemy setup
engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Create database tables
async def create_tables():
    """
    Create all database tables that are defined using SQLAlchemy models.
    Called during application startup.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")

# Dependency for getting DB session
async def get_db():
    """
    Dependency function that yields db sessions
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Function to close database connections on shutdown
async def close_db_connections():
    """
    Close all database connections when shutting down the application.
    Called during application shutdown.
    """
    try:
        await engine.dispose()
        print("Database connections closed successfully")
    except Exception as e:
        print(f"Error closing database connections: {e}")
        raise 