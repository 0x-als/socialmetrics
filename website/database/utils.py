from database.session import get_session
from utils import security
from utils.logger import logger_config
from sqlalchemy import *
from database.models import *


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


class VkontakteRepo:
    def __init__(self):
        self.log_file = "VkontakteRepo.log"

    async def get_sessions(self):
        logger = logger_config(name="get_sessions", log_file=self.log_file)

        try:

            async with get_session() as session:

                try:

                    query = select(ScrapeAccounts).where(
                        ScrapeAccounts.type == "vk",
                        ScrapeAccounts.status.is_(True)
                    )
                    result = await session.execute(query)
                    return result.scalars().all()

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)

    async def create_session(self, client_id: str, api_key: str, profile_path: str):
        logger = logger_config(name="create_session", log_file=self.log_file)

        try:

            enc_client_id = await security.encrypt(client_id)
            enc_api_key = await security.encrypt(api_key)

            async with get_session() as session:

                try:

                    account = ScrapeAccounts(
                        client_id=enc_client_id,
                        api_key=enc_api_key,
                        path=profile_path,
                        type="vk"
                    )
                    session.add(account)
                    await session.commit()
                    return True

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False

    async def update_token_hash(self, session_id, token_hash):
        logger = logger_config(name="update_token_hash", log_file=self.log_file)

        try:

            async with get_session() as session:
                try:

                    query = update(ScrapeAccounts).where(ScrapeAccounts.id == session_id).values(token_hash=token_hash)
                    await session.execute(query)
                    await session.commit()
                    logger.info(f"Token_hash was updated for vk_session: {session_id}")
                    return True

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False


class YoutubeRepo:
    def __init__(self):
        self.log_file = "YoutubeRepo.log"

    async def create_session(self, api_key):
        logger = logger_config(name="create_session", log_file=self.log_file)

        try:

            enc_api_key = await security.encrypt(api_key)

            async with get_session() as session:
                try:

                    account = ScrapeAccounts(
                        api_key=enc_api_key,
                        type="youtube"
                    )
                    session.add(account)
                    await session.commit()
                    return True


                except Exception as ex:
                    logger.exception(ex)
                    return False

        except ExceptionGroup as ex:
            logger.exception(ex)
            return False


class TelegramRepo:
    def __init__(self):
        self.log_file = "TelegramRepo.log"

    async def create_session(self, phone, api_id, api_hash):
        logger = logger_config(name="create_session", log_file=self.log_file)

        try:

            enc_api_id = await security.encrypt(str(api_id))
            enc_api_hash = await security.encrypt(str(api_hash))

            async with get_session() as session:

                try:

                    account = ScrapeAccounts(
                        api_key=enc_api_id,
                        token_hash=enc_api_hash,
                        path=f"{phone}.session",
                        type="telegram",
                        status=True
                    )
                    session.add(account)
                    await session.commit()
                    return True

                except Exception as ex:
                    await session.rollback()
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False


class TelegramBotRepo:
    def __init__(self):
        self.log_file = "TelegramBotRepo.log"

    async def create_telegram_bot(self, token, bot_name, bon_username):
        logger = logger_config(name="create_telegram_bot", log_file=self.log_file)

        try:

            async with get_session() as session:
                try:

                    token_hash = await security.encrypt(token)
                    url = f"https://t.me/{bon_username}"

                    telegram_bot = TelegramBots(
                        token_hash=token_hash,
                        bot_name=bot_name,
                        url=url
                    )
                    session.add(telegram_bot)
                    await session.commit()
                    return True

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False

    async def get_telegram_bots(self):
        logger = logger_config(name="get_telegram_bots", log_file=self.log_file)

        try:

            async with get_session() as session:
                try:

                    query = select(TelegramBots)
                    result = await session.execute(query)
                    return result.scalars().all()

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False

    async def delete_telegram_bot(self, telegram_bot_id):
        logger = logger_config(name="delete_telegram_bot", log_file=self.log_file)

        try:

            async with get_session() as session:

                try:

                    query = delete(TelegramBots).where(TelegramBots.id == telegram_bot_id)
                    result = await session.execute(query)
                    await session.commit()

                    return result.rowcount > 0

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False


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


class ScrapeAccountsRepo:
    def __init__(self):
        self.log_file = "ScrapeAccountsRepo.log"

    async def get_scrape_accounts(self):
        logger = logger_config(name="get_scrape_accounts", log_file=self.log_file)

        try:

            async with get_session() as session:

                try:

                    query = select(ScrapeAccounts)
                    result = await session.execute(query)
                    return result.scalars().all()

                except Exception as ex:
                    logger.exception(ex)
                    return False

        except Exception as ex:
            logger.exception(ex)
            return False

    async def delete_scrape_account(self, scrape_account_id):
        logger = logger_config(name="delete_scrape_account", log_file=self.log_file)

        try:

            async with get_session() as session:

                try:

                    query = delete(ScrapeAccounts).where(ScrapeAccounts.id == scrape_account_id)
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


class SocialNetworksRepo:
    def __init__(self):
        self.log_file = "AccountsRepo.log"

    async def get_social_networks(self, user_id):
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
