from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import config

# synchronous engine/session (existing)
sql_url = URL.create("postgresql+psycopg2",
                    username=config.DB_USER,
                    password=config.DB_PASSWORD,
                    host=config.DB_HOST,
                    port=config.DB_PORT,
                    database=config.DB_NAME)

engine = create_engine(sql_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# asynchronous engine/session
async_sql_url = URL.create("postgresql+asyncpg",
                           username=config.DB_USER,
                           password=config.DB_PASSWORD,
                           host=config.DB_HOST,
                           port=config.DB_PORT,
                           database=config.DB_NAME)

async_engine = create_async_engine(async_sql_url, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
    