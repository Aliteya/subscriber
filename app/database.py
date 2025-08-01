from .settings import settings
from .models import Base
from .logging import logger

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(settings.get_url(), echo=True)

async def init_db():
    logger.info("Initialize connection")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db_connections():
    try:
        await engine.dispose()
        logger.debug("Connection close")
    except Exception as e:
        logger.error(f"Close connections error")
        raise e
    
AsyncSessionLocal=sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session