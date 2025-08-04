import json
import asyncio
from sqlalchemy.exc import SQLAlchemyError

# from .settings import settings
from .models import Log
from .schemas import UserInput
from .database import init_db, get_session
from .logging import logger

# asyncio.run(init_db())

async def process_record(record: dict):
    try:
        message_body = record['body']
        logger.debug(f"user input: {message_body}")
        user_input = UserInput.model_validate_json(message_body)
        
        async for session in get_session():
            try:
                log = Log(name_recipient=user_input.name, reason=user_input.reason)
                session.add(log)
                await session.commit()
                logger.debug("message saved in database")
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Database error: {e}")
                raise e

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error decoding SQS message: {e}. Message will be discarded.")
        pass
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise e

async def a_lambda_handler(event: dict, context: object):

    processing_tasks = [process_record(record) for record in event.get('Records', [])]
    
    results = await asyncio.gather(*processing_tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Batch processing failed due to an exception: {result}")
            raise result

    logger.info(f"Successfully processed {len(results)} messages.")
    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete')
    }

def lambda_handler(event: dict, context: object):
    return asyncio.run(a_lambda_handler(event, context))