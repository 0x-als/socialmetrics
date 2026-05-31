from database.utils.scrape_accounts import *
from database.utils.session import *
from database.utils.users import *
from database.utils.vkontakte import *
from database.utils.telegram import *
from database.utils.telegram_bot import *
from database.utils.proxies import *
from database.utils.instagram import *
from database.utils.youtube import *
from database.utils.social_network import *
from database.utils.settings import *


class INITDatabase:
    def __init__(self):
        self.settings_repo = SettingsRepo()
        self.users_repo = UsersRepo()
        self.session_repo = SessionRepo()
        self.vkontakte_repo = VkontakteRepo()
        self.scrape_accounts_repo = ScrapeAccountsRepo()
        self.youtube_repo = YoutubeRepo()
        self.telegram_bot_repo = TelegramBotRepo()
        self.social_networks_repo = SocialNetworksRepo()
        self.telegram_repo = TelegramRepo()
        self.proxies_repo = ProxiesRepo()
        self.instagram_repo = InstagramRepo()


init_database = INITDatabase()
