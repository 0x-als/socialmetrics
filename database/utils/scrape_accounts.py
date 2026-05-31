from config import *
from utils import security
from database.models import *
from sqlalchemy import *
from utils.logger import logger_config
from database.session import get_session
from sqlalchemy.ext.asyncio import create_async_engine

class ScrapeAccountsRepo:
    def __init__(self):
        self.log_file = "ScrapeAccountsRepo.log"

    async def get_scrape_accounts(self):
        logger = logger_config(name="get_scrape_accounts", log_file=self.log_file)

        try:

            async with get_session() as session:

                try:

                    query = select(ScrapeAccounts)
                    result = await session.execute(query)
                    return result.scalars().all()

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False

    async def delete_scrape_account(self, scrape_account_id):
        logger = logger_config(name="delete_scrape_account", log_file=self.log_file)

        try:

            async with get_session() as session:

                try:

                    query = delete(ScrapeAccounts).where(ScrapeAccounts.id == scrape_account_id)
                    result = await session.execute(query)
                    await session.commit()

                    return result.rowcount > 0

                except Exception as ex:
                    await session.rollback()
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False