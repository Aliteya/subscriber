from .settings import settings
from .models import Base
from .logging import logger
import boto3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

engine = None
SessionLocal = None

ssm_client = boto3.client("ssm")
def get_ssm_parameter(parameter_name: str) -> str:
    logger.debug(f"Fetching SSM parameter: {parameter_name}")
    response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
    return response['Parameter']['Value']

def init_db():
    global engine, SessionLocal

    if engine is not None:
        return

    logger.info("Initializing database connection...")

    db_host = get_ssm_parameter(settings.DATABASE_HOST)
    db_port = get_ssm_parameter(settings.DATABASE_PORT)
    db_user = get_ssm_parameter(settings.DATABASE_USER)
    db_pass = get_ssm_parameter(settings.DATABASE_PASSWORD)
    db_name = get_ssm_parameter(settings.DATABASE_NAME)

    db_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    engine = create_engine(db_url)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

def get_session():
    if SessionLocal is None:
        init_db()
    
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()