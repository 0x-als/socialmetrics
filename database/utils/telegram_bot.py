from config import *
from utils import security
from database.models import *
from sqlalchemy import *
from utils.logger import logger_config
from database.session import get_session
from sqlalchemy.ext.asyncio import create_async_engine

class TelegramBotRepo:
    def __init__(self):
        self.log_file = "TelegramBotRepo.log"

    async def create_telegram_bot(self, token, bot_name, bon_username):
        logger = logger_config(name="create_telegram_bot", log_file=self.log_file)

        try:

            async with get_session() as session:
                try:

                    token_hash = await security.encrypt(token)
                    url = f"https://t.me/{bon_username}"

                    telegram_bot = TelegramBots(
                        token_hash=token_hash,
                        bot_name=bot_name,
                        url=url
                    )
                    session.add(telegram_bot)
                    await session.commit()
                    return True

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False

    async def get_telegram_bots(self):
        logger = logger_config(name="get_telegram_bots", log_file=self.log_file)

        try:

            async with get_session() as session:
                try:

                    query = select(TelegramBots)
                    result = await session.execute(query)
                    return result.scalars().all()

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False

    async def delete_telegram_bot(self, telegram_bot_id):
        logger = logger_config(name="delete_telegram_bot", log_file=self.log_file)

        try:

            async with get_session() as session:

                try:

                    query = delete(TelegramBots).where(TelegramBots.id == telegram_bot_id)
                    result = await session.execute(query)
                    await session.commit()

                    return result.rowcount > 0

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False