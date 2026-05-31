from config import *
from utils import security
from database.models import *
from sqlalchemy import *
from utils.logger import logger_config
from database.session import get_session
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.dialects.postgresql import insert



class InstagramRepo:
    def __init__(self):
        self.log_file = "InstagramRepo.log"

    async def get_instagram_accounts(self):
        logger = logger_config(name="get_instagram_accounts", log_file=self.log_file)

        try:

            async with get_session() as session:
                try:

                    query = select(SocialNetworks).where(SocialNetworks.type == "instagram")
                    result = await session.execute(query)
                    return result.scalars().all()

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)

    from sqlalchemy.dialects.postgresql import insert

    async def save_network_items(self, data):
        logger = logger_config(name="save_network_items", log_file=self.log_file)

        objects = []

        try:
            async with get_session() as session:
                try:
                    for item in data:
                        row = item[0]

                        network_id = row["id"]
                        shortcodes = row["shortcodes"]

                        for shortcode in shortcodes:
                            objects.append({
                                "_network_id": network_id,
                                "url": f"https://www.instagram.com/p/{shortcode}/",
                                "status": True
                            })

                    if objects:
                        stmt = (
                            insert(NetworkItems)
                            .values(objects)
                            .on_conflict_do_nothing(
                                index_elements=["_network_id", "url"]
                            )
                        )

                        await session.execute(stmt)
                        await session.commit()

                        logger.info(f"Saved {len(objects)} network items (duplicates skipped)")

                except Exception as ex:
                    logger.exception(ex)

        except Exception as ex:
            logger.exception(ex)
