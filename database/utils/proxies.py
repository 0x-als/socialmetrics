from config import *
from utils import security
from database.models import *
from sqlalchemy import *
from utils.logger import logger_config
from database.session import get_session
from sqlalchemy.ext.asyncio import create_async_engine

class ProxiesRepo:
    def __init__(self):
        self.log_file = "ProxiesRepo.log"

    async def get_proxies(self):
        logger = logger_config(name="get_proxies", log_file=self.log_file)

        try:

            async with get_session() as session:
                try:

                    query = select(Proxies)
                    result = await session.execute(query)
                    return result.scalars().all()

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False

    async def get_proxies_true(self):
        logger = logger_config(name="get_proxies_true", log_file=self.log_file)

        try:

            async with get_session() as session:
                try:

                    query = select(Proxies).where(Proxies.status == True)
                    result = await session.execute(query)
                    return result.scalars().all()

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)

    async def create_proxies(self, proxies_data: list):
        logger = logger_config(name="create_proxies", log_file=self.log_file)
        try:
            async with get_session() as session:
                try:
                    added = 0
                    for p in proxies_data:
                        proxy = Proxies(
                            host=p.get("host"),
                            port=p.get("port"),
                            login=p.get("login"),
                            password_hash=await security.encrypt(p.get("password")),
                            status=True
                        )
                        session.add(proxy)
                        added += 1

                    await session.commit()
                    return added

                except Exception as ex:
                    await session.rollback()
                    logger.exception(ex)
                    return 0
        except Exception as ex:
            logger.exception(ex)
            return 0

    async def delete_proxy(self, proxy_id: int):
        logger = logger_config(name="delete_proxy", log_file=self.log_file)
        try:
            async with get_session() as session:
                try:
                    query = delete(Proxies).where(Proxies.id == proxy_id)
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