from sqlalchemy import *
from database.models import *
from utils.logger import logger_config
from sqlalchemy.orm import selectinload
from database.session import get_session
from sqlalchemy.dialects.postgresql import insert


class TikTokRepo:
    def __init__(self):
        self.log_file = "TikTokRepo.log"

    async def save_network_items(self, data):
        logger = logger_config(name="save_network_items", log_file=self.log_file)

        objects = []

        try:
            async with get_session() as session:
                try:
                    for item in data:
                        row = item[0]

                        network_id = row["id"]
                        urls = row["urls"]

                        for url in urls:
                            objects.append({
                                "_network_id": network_id,
                                "url": url,
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
