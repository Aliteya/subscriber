import json
from sqlalchemy.exc import SQLAlchemyError

from models import Log
from schemas import UserInput
from database import init_db, get_session # Импортируем синхронные функции
from mylogging import logger

try:
    init_db()
    logger.info("Database connection initialized successfully.")
except Exception as e:
    logger.critical(f"FATAL: Failed to initialize database connection on startup: {e}")
    raise e

def process_record(record: dict):
    try:
        message_body = record['body']
        logger.debug(f"user input: {message_body}")
        user_input = UserInput.model_validate_json(message_body)
        
        for session in get_session():
            try:
                log = Log(name_recipient=user_input.name, reason=user_input.reason)
                session.add(log)
                session.commit()
                logger.debug("message saved in database")
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Database error: {e}")
                raise e

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error decoding SQS message: {e}. Message will be discarded.")
        pass
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise e

def lambda_handler(event: dict, context: object):
    for record in event.get('Records', []):
        try:
            process_record(record)
        except Exception as e:
            logger.error(f"Failed to process record {record.get('messageId')}. Error: {e}")

    logger.info(f"Successfully processed {len(event.get('Records', []))} messages.")
    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete')
    }