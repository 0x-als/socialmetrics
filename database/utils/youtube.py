from config import *
from utils import security
from database.models import *
from sqlalchemy import *
from utils.logger import logger_config
from database.session import get_session
from sqlalchemy.ext.asyncio import create_async_engine


class YoutubeRepo:
    def __init__(self):
        self.log_file = "YoutubeRepo.log"

    async def create_session(self, api_key):
        logger = logger_config(name="create_session", log_file=self.log_file)

        try:

            enc_api_key = await security.encrypt(api_key)

            async with get_session() as session:
                try:

                    account = ScrapeAccounts(
                        api_key=enc_api_key,
                        type="youtube"
                    )
                    session.add(account)
                    await session.commit()
                    return True


                except Exception as ex:
                    logger.exception(ex)
                    return False

        except ExceptionGroup as ex:
            logger.exception(ex)
            return False
