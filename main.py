import asyncio

import uvicorn

from config import *
from database import init_database
from utils.security import load_key
from utils.logger import logger_config


class Boot:
    def __init__(self):
        self.log_file = "Boot.log"

    async def system(self):
        logger = logger_config(name="system", log_file=self.log_file)
        try:

            load_key(config_key["key"]["secret_key"])

            await init_database.settings_repo.create_models()
            await init_database.settings_repo.create_roles()
            await init_database.settings_repo.create_staff()

        except Exception as ex:
            logger.exception(ex)

    async def website(self):
        logger = logger_config(name="website", log_file=self.log_file)

        try:

            config = uvicorn.Config(
                app="website.app:app",
                host="localhost",
                port=8000,
                loop="asyncio",
                reload=False,
            )
            server = uvicorn.Server(config=config)
            await server.serve()

        except Exception as ex:
            logger.exception(ex)

    async def main(self):
        logger = logger_config(name="main", log_file=self.log_file)

        try:

            await self.system()
            await self.website()

        except Exception as ex:
            logger.exception(ex)


if __name__ == "__main__":
    asyncio.run(Boot().main())
