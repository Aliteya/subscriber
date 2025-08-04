import json
from sqlalchemy.exc import SQLAlchemyError

# from .settings import settings
from .models import Log
from .schemas import UserInput
from .database import init_db, get_session # Импортируем синхронные функции
from .logging import logger

def process_record(record: dict):
    """Обрабатывает одну запись из SQS."""
    try:
        message_body = record['body']
        logger.debug(f"user input: {message_body}")
        user_input = UserInput.model_validate_json(message_body)
        
        # Получаем сессию с помощью with, чтобы она автоматически закрылась
        for session in get_session():
            try:
                log = Log(name_recipient=user_input.name, reason=user_input.reason)
                session.add(log)
                session.commit()
                logger.debug("message saved in database")
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Database error: {e}")
                # Пробрасываем ошибку дальше, чтобы SQS мог повторить обработку сообщения
                raise e

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error decoding SQS message: {e}. Message will be discarded.")
        # Не пробрасываем ошибку, т.к. повторная обработка не поможет
        pass
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        # Пробрасываем другие неожиданные ошибки
        raise e

def lambda_handler(event: dict, context: object):
    # Убедимся, что БД инициализирована перед началом работы
    init_db()

    # Обрабатываем записи последовательно в цикле
    for record in event.get('Records', []):
        try:
            process_record(record)
        except Exception as e:
            # Если обработка одного сообщения провалилась, логируем и продолжаем
            # В зависимости от требований, можно остановить всю обработку
            logger.error(f"Failed to process record {record.get('messageId')}. Error: {e}")
            # Можно здесь пробросить исключение, чтобы весь батч был помечен как неудачный
            # raise e

    logger.info(f"Successfully processed {len(event.get('Records', []))} messages.")
    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete')
    }