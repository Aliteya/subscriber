from .settings import settings
from .models import Base
from .logging import logger
import boto3
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = None
AsyncSessionLocal = None

ssm_client = boto3.client("ssm")
def get_ssm_parameter(parameter_name: str) -> str:
    logger.debug(f"Fetching SSM parameter: {parameter_name}")
    response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
    return response['Parameter']['Value']

async def init_db():
    global engine, AsyncSessionLocal

    if engine is not None:
        return

    logger.info("Initializing database connection...")

    db_host = get_ssm_parameter(settings.DATABASE_HOST)
    db_port = get_ssm_parameter(settings.DATABASE_PORT)
    db_user = get_ssm_parameter(settings.DATABASE_USER)
    db_pass = get_ssm_parameter(settings.DATABASE_PASSWORD)
    db_name = get_ssm_parameter(settings.DATABASE_NAME)

    db_url = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    engine = create_async_engine(db_url)
    AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_session():
    if AsyncSessionLocal is None:
        await init_db()
    
    async with AsyncSessionLocal() as session:
        yield session