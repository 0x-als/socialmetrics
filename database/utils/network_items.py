from sqlalchemy.orm import selectinload
from sqlalchemy.dialects.postgresql import insert

from config import *
from utils import security
from database.models import *
from sqlalchemy import *
from utils.logger import logger_config
from database.session import get_session


class NetworkItemsRepo:
    def __init__(self):
        self.log_file = "NetworkItemsRepo.log"

    async def update_published_at(self, items: list[dict]):
        logger = logger_config(name="update_published_at", log_file=self.log_file)

        try:
            async with get_session() as session:
                try:
                    ids = []
                    case_map = {}

                    for entry in items:
                        published_at = entry["metadata"].get("published_at")
                        if not published_at:
                            continue

                        dt = datetime.strptime(published_at, "%Y-%m-%d %H:%M:%S")

                        item_id = entry["network_item_id"]
                        ids.append(item_id)
                        case_map[item_id] = dt

                    if not ids:
                        return True

                    stmt = (
                        update(NetworkItems)
                        .where(
                            NetworkItems.id.in_(ids),
                            NetworkItems.published_at.is_(None)
                        )
                        .values(
                            published_at=case(case_map, value=NetworkItems.id)
                        )
                    )

                    await session.execute(stmt)
                    await session.commit()

                except Exception as ex:
                    await session.rollback()
                    logger.exception(ex)

        except Exception as ex:
            logger.exception(ex)

    async def get_network_items_by_type(self, type: str):
        logger = logger_config(name="get_instagram_items", log_file=self.log_file)

        try:

            async with get_session() as session:
                try:

                    query = (
                        select(NetworkItems)
                        .join(SocialNetworks)
                        .where(SocialNetworks.type == type)
                        .options(selectinload(NetworkItems.network))
                    )
                    result = await session.execute(query)
                    return result.scalars().all()

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False