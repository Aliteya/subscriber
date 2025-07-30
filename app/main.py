import boto3
import json
import time
import asyncio
from sqlalchemy.exc import SQLAlchemyError

from .settings import settings
from .models import Log
from .schemas import UserInput
from .database import init_db, close_db_connections, get_session
from .logging import logger

sqs_client = boto3.client(
    "sqs",
    region_name=settings.get_aws_region(),
    aws_access_key_id=settings.get_access_key_id(),
    aws_secret_access_key=settings.get_access_secret_key()
)


async def process_message(message: dict):
    try: 
        message_body = message['Body']
        logger.debug(f"user input: {message_body}")
        user_input = UserInput.model_validate_json(message_body)
        async for session in get_session():
            try:        
                log = Log(name_recipient=user_input.name, reason=user_input.reason)
                session.add(log)
                await session.commit()
                logger.debug("message saved in database")
                return True
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Database error: {e}")
                return False
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error decoding SQS message: {e}")
        return True # Считаем обработанным, чтобы не зацикливаться на битом сообщении
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False

async def main():
    logger.info("SQS worker started. Waiting for messages...")
    try: 
        await init_db()
        logger.debug("init database")
        while True:
            try:
                
                response = sqs_client.receive_message(
                    QueueUrl=settings.get_sqs_url(),
                    MaxNumberOfMessages=5,
                    WaitTimeSeconds=20
                )
                messages = response.get('Messages', [])
                if not messages:
                    continue
                for message in messages:
                    if await process_message(message):
                        sqs_client.delete_message(
                            QueueUrl=settings.get_sqs_url(),
                            ReceiptHandle=message['ReceiptHandle']
                        )
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(10)
    finally:
        await close_db_connections()
        logger.debug("close database connections")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Worker stopped by user.")