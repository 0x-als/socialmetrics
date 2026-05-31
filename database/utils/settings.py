from config import *
from utils import security
from database.models import *
from sqlalchemy import *
from utils.logger import logger_config
from database.session import get_session
from sqlalchemy.ext.asyncio import create_async_engine

class SettingsRepo:
    def __init__(self):
        self.log_file = "SettingsRepo.log"

    async def create_models(self):
        logger = logger_config(name="create_models", log_file=self.log_file)

        try:

            database_url = config_database["database_url"].format(**config_database["database"])

            engine = create_async_engine(
                database_url,
                echo=False,
                future=True,
            )

            async with engine.begin() as connect:
                await connect.run_sync(BaseModel.metadata.create_all)

            await engine.dispose()
            logger.info(f"Database created successfully")

        except Exception as ex:
            logger.exception(f"Database creation failed: {ex}")

    async def create_roles(self):
        logger = logger_config(name="create_roles", log_file=self.log_file)

        try:
            roles = [
                {"title": "admin", "description": "Administrator"},
                {"title": "moderator", "description": "Moderator"},
                {"title": "user", "description": "User"},
            ]

            async with get_session() as session:
                try:
                    for role_data in roles:
                        query = select(Roles).where(Roles.title == role_data["title"])
                        result = await session.execute(query)
                        existing_role = result.scalar_one_or_none()

                        if existing_role:
                            logger.info(f"Role: {existing_role.title} already exists")
                            continue

                        new_role = Roles(
                            title=role_data["title"],
                            description=role_data["description"]
                        )

                        session.add(new_role)
                        logger.info(f"Role: {role_data['title']} created")

                    await session.commit()

                except Exception as ex:
                    await session.rollback()
                    logger.exception(f"Roles creation failed: {ex}")

        except Exception as ex:
            logger.exception(ex)

    async def create_staff(self):
        logger = logger_config(name="create_staff", log_file=self.log_file)

        try:
            async with get_session() as session:
                try:
                    staff_list = [
                        {"login": "admin", "role": "admin"},
                        {"login": "moderator", "role": "moderator"},
                    ]

                    for staff in staff_list:
                        login = staff["login"]
                        role_title = staff["role"]

                        # Проверяем пользователя
                        user_query = select(Users).where(Users.login == login)
                        user_result = await session.execute(user_query)
                        user = user_result.scalar_one_or_none()

                        if user:
                            logger.info(f"User: {login} already exists")
                            continue

                        # Проверяем роль
                        role_query = select(Roles).where(Roles.title == role_title)
                        role_result = await session.execute(role_query)
                        role = role_result.scalar_one_or_none()

                        if not role:
                            logger.warning(f"Role '{role_title}' not exists — creating roles")
                            await self.create_roles()

                            # повторный запрос роли
                            role_result = await session.execute(role_query)
                            role = role_result.scalar_one_or_none()

                            if not role:
                                logger.error(f"Role '{role_title}' still not found after creation!")
                                continue

                        encrypted_password = await security.encrypt(login)

                        new_user = Users(
                            login=login,
                            password_hash=encrypted_password,
                            _role_id=role.id,
                        )

                        session.add(new_user)
                        await session.commit()
                        logger.info(f"User: {login} created successfully!")

                except Exception as ex:
                    logger.exception(f"Staff creation failed: {ex}")

        except Exception as ex:
            logger.exception(ex)