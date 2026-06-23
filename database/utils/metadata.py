from database.models import *
from sqlalchemy import *
from utils.logger import logger_config
from database.session import get_session
from sqlalchemy.dialects.postgresql import insert


class ItemMetadataRepo:
    def __init__(self):
        self.log_file = "MetadataRepo.log"

    async def save_metadata(self, items: list[dict]):
        logger = logger_config(name="save_metadata", log_file=self.log_file)
        try:

            async with get_session() as session:
                try:
                    rows = [
                        {
                            "_item_id": entry["network_item_id"],
                            "likes": entry["metadata"].get("likes", 0),
                            "views_picture": entry["metadata"].get("video_views_count", 0),
                            "views_video": entry["metadata"].get("video_play_count", 0),
                            "description": entry["metadata"].get("caption") or "",
                            "saves": entry["metadata"].get("saves", 0),
                            "reposts": entry["metadata"].get("shares", 0),
                            "comments_count": entry["metadata"].get("comments_count", 0),
                        }
                        for entry in items
                    ]

                    await session.execute(insert(ItemMetadata), rows)
                    await session.commit()

                except Exception as ex:
                    await session.rollback()
                    logger.exception(ex)

        except Exception as ex:
            logger.exception(ex)