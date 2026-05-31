from config import *
from utils import security
from database.models import *
from sqlalchemy import *
from utils.logger import logger_config
from database.session import get_session
from sqlalchemy.ext.asyncio import create_async_engine

class TelegramRepo:
    def __init__(self):
        self.log_file = "TelegramRepo.log"

    async def create_session(self, phone, api_id, api_hash):
        logger = logger_config(name="create_session", log_file=self.log_file)

        try:

            enc_api_id = await security.encrypt(str(api_id))
            enc_api_hash = await security.encrypt(str(api_hash))

            async with get_session() as session:

                try:

                    account = ScrapeAccounts(
                        api_key=enc_api_id,
                        token_hash=enc_api_hash,
                        path=f"{phone}.session",
                        type="telegram",
                        status=True
                    )
                    session.add(account)
                    await session.commit()
                    return True

                except Exception as ex:
                    await session.rollback()
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False