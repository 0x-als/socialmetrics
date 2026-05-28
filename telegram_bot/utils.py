import requests
from utils.logger import logger_config


async def get_telegram_bot_name(token: str) -> str:
    logger = logger_config(name='telegram_bot_name', log_file='TelegramBotUtils.log')

    try:

        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url).json()
        return response["result"]["first_name"]

    except Exception as ex:
        logger.error(ex)
        return False


async def get_telegram_bot_username(token: str) -> str:
    logger = logger_config(name='telegram_bot_username', log_file='TelegramBotUtils.log')

    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url).json()

        return response["result"]["username"]

    except Exception as ex:
        logger.error(ex)
        return False
