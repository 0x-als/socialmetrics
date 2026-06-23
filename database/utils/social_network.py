from typing import Any, Sequence

from config import *
from utils import security
from database.models import *
from sqlalchemy import *
from utils.logger import logger_config
from database.session import get_session
from sqlalchemy.ext.asyncio import create_async_engine


class SocialNetworksRepo:
    def __init__(self):
        self.log_file = "AccountsRepo.log"

    async def get_social_networks_by_user_id(self, user_id: object) -> Sequence[Any] | bool:
        logger = logger_config(name="get_accounts", log_file=self.log_file)

        try:

            async with get_session() as session:

                try:

                    query = select(SocialNetworks).where(SocialNetworks._user_id == user_id)
                    result = await session.execute(query)
                    return result.scalars().all()

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False

    async def get_social_networks_by_type(self, type: str):
        logger = logger_config(name="get_social_networks_by_type", log_file=self.log_file)

        try:

            async with get_session() as session:
                try:

                    query = select(SocialNetworks).where(SocialNetworks.type == type)
                    result = await session.execute(query)
                    return result.scalars().all()

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)

    async def create_social_network(self, data):
        logger = logger_config(name="create_social_networks", log_file=self.log_file)

        try:

            async with get_session() as session:

                try:

                    network = SocialNetworks(
                        _user_id=data["user_id"],
                        username=data["username"],
                        url=data["url"],
                        type=data["type"],
                        status=True
                    )

                    session.add(network)
                    await session.commit()
                    return True

                except Exception as ex:
                    await session.rollback()
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False

    async def delete_social_network(self, social_network_id):
        logger = logger_config(name="delete_social_network", log_file=self.log_file)

        try:

            async with get_session() as session:

                try:

                    query = delete(SocialNetworks).where(SocialNetworks.id == social_network_id)
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
