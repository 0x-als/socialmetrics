from config import *
from utils import security
from database.models import *
from sqlalchemy import *
from utils.logger import logger_config
from database.session import get_session
from sqlalchemy.ext.asyncio import create_async_engine

class UsersRepo:
    def __init__(self):
        self.log_file = "UsersRepo.log"

    async def get_all_users(self):
        logger = logger_config(name="get_all_users", log_file=self.log_file)

        try:

            async with get_session() as session:

                try:

                    query = select(Users).order_by(Users.login)
                    result = await session.execute(query)
                    return result.scalars().all()

                except Exception as ex:
                    logger.exception(ex)
                    return []

        except Exception as ex:
            logger.exception(ex)
            return []

    async def get_user_by_id(self, _user_id: int):
        logger = logger_config(name="get_user_by_id", log_file=self.log_file)

        try:

            async with get_session() as session:
                try:

                    query = select(Users).where(Users.id == _user_id)
                    result = await session.execute(query)
                    user = result.scalar_one_or_none()

                    if user:
                        return user

                    else:
                        return None

                except Exception as ex:
                    logger.exception(ex)
                    return None

        except Exception as ex:
            logger.exception(ex)
            return None

    async def get_user_login(self, login):
        logger = logger_config(name="get_user_login", log_file=self.log_file)

        try:

            async with get_session() as session:
                try:

                    query = select(Users).where(Users.login == login)
                    result = await session.execute(query)
                    user = result.scalar_one_or_none()

                    if user:
                        return user

                    else:
                        return None

                except Exception as ex:
                    logger.exception(ex)

        except Exception as ex:
            logger.exception(ex)