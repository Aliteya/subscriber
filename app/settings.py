from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class SubscriberSettings(BaseSettings):
    DATABASE_HOST: str
    DATABASE_PORT: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_NAME: str
    # AWS_REGION: str
    SQS_QUEUE_URL: str
    # AWS_ACCESS_KEY_ID: str
    # AWS_SECRET_ACCESS_KEY: str

    model_config = SettingsConfigDict(env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "./../.env"), extra="ignore")

    def get_url(self) -> str:
        return f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    # def get_aws_region(self) -> str:
    #     return self.AWS_REGION
    
    def get_sqs_url(self) -> str:
        return self.SQS_QUEUE_URL
    
    # def get_access_key_id(self):
    #     return self.AWS_ACCESS_KEY_ID
    
    # def get_access_secret_key(self):
    #     return self.AWS_SECRET_ACCESS_KEY

settings = SubscriberSettings()