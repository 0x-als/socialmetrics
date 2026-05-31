from config import *
from utils import security
from database.models import *
from sqlalchemy import *
from utils.logger import logger_config
from database.session import get_session
from sqlalchemy.ext.asyncio import create_async_engine

class SessionRepo:
    def __init__(self):
        self.log_file = "SessionRepo.log"

    async def get_session_by_token(self, token: str):
        logger = logger_config(name="get_session_by_token", log_file=self.log_file)

        try:

            async with get_session() as session:
                try:

                    query = select(Session).where(Session.token == token)
                    result = await session.execute(query)
                    return result.scalar_one_or_none()

                except Exception as ex:
                    logger.exception(ex)
                    return None

        except Exception as ex:
            logger.exception(ex)
            return None

    async def create_session(self, _user_id, token):
        logger = logger_config(name="create_session", log_file=self.log_file)

        try:

            async with get_session() as session:
                new_session = Session(
                    _user_id=_user_id,
                    token=token["token"],
                    expires_at=token["expires_at"]
                )

                session.add(new_session)
                await session.commit()

            return True

        except Exception as ex:
            logger.exception(ex)
            return False

    async def update_session(self, session_id, expires_at):
        logger = logger_config(name="update_session", log_file=self.log_file)

        try:

            async with get_session() as session:
                try:

                    query = select(Session).where(Session.id == session_id)
                    result = await session.execute(query)
                    token_session = result.scalar_one_or_none()

                    if token_session:
                        token_session.expires_at = expires_at
                        await session.commit()
                        return True

                except Exception as ex:
                    await session.rollback()
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False

    async def delete_session_by_token(self, token):
        logger = logger_config(name="delete_session_by_token", log_file=self.log_file)

        try:
            async with get_session() as session:
                try:

                    query = select(Session).where(Session.token == token)
                    result = await session.execute(query)
                    token_session = result.scalar_one_or_none()
                    if token_session:
                        await session.delete(token_session)
                        await session.commit()
                    else:
                        return False
                except Exception as ex:
                    logger.exception(ex)
                    return False


        except Exception as ex:
            logger.exception(ex)
            return False