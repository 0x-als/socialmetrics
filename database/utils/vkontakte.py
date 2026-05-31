from config import *
from utils import security
from database.models import *
from sqlalchemy import *
from utils.logger import logger_config
from database.session import get_session
from sqlalchemy.ext.asyncio import create_async_engine


class VkontakteRepo:
    def __init__(self):
        self.log_file = "VkontakteRepo.log"

    async def get_sessions(self):
        logger = logger_config(name="get_sessions", log_file=self.log_file)

        try:

            async with get_session() as session:

                try:

                    query = select(ScrapeAccounts).where(
                        ScrapeAccounts.type == "vk",
                        ScrapeAccounts.status.is_(True)
                    )
                    result = await session.execute(query)
                    return result.scalars().all()

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)

    async def create_session(self, client_id: str, api_key: str, profile_path: str):
        logger = logger_config(name="create_session", log_file=self.log_file)

        try:

            enc_client_id = await security.encrypt(client_id)
            enc_api_key = await security.encrypt(api_key)

            async with get_session() as session:

                try:

                    account = ScrapeAccounts(
                        client_id=enc_client_id,
                        api_key=enc_api_key,
                        path=profile_path,
                        type="vk"
                    )
                    session.add(account)
                    await session.commit()
                    return True

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False

    async def update_token_hash(self, session_id, token_hash):
        logger = logger_config(name="update_token_hash", log_file=self.log_file)

        try:

            async with get_session() as session:
                try:

                    query = update(ScrapeAccounts).where(ScrapeAccounts.id == session_id).values(token_hash=token_hash)
                    await session.execute(query)
                    await session.commit()
                    logger.info(f"Token_hash was updated for vk_session: {session_id}")
                    return True

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False
