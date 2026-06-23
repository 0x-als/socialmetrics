from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from config import config_telegram, base_dir
from utils.logger import logger_config
import os


class AuthorizationTelegram(TelegramClient):
    def __init__(self, phone, api_id, api_hash):
        self.phone = phone
        self.log_file = "AuthorizationTelegram.log"

        session_dir = f"{base_dir}/files/profiles/telegram_profile"
        os.makedirs(session_dir, exist_ok=True)

        session_path = f"{session_dir}/{phone}"

        super().__init__(
            session=session_path,
            api_id=api_id,
            api_hash=api_hash,
            device_model=config_telegram["telethon"]["device_model"],
            system_version=config_telegram["telethon"]["system_version"],
            app_version=config_telegram["telethon"]["app_version"]
        )

    async def start(self):
        await self.connect()
        return await self.send_code_request(self.phone)

    async def confirm_code(self, code):
        try:
            await self.sign_in(self.phone, code)
            await self.disconnect()
            return {"status": True}
        except SessionPasswordNeededError:
            return {"status": "password_required"}
        except Exception as ex:
            await self.disconnect()
            return {"status": False, "message": str(ex)}


