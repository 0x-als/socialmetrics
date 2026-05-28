import hmac
import string
import secrets
import hashlib

from config import *
from pathlib import Path
from utils.logger import logger_config
from cryptography.fernet import Fernet
from datetime import timedelta, datetime, timezone


def load_key(path_key: Path) -> bytes:
    logger = logger_config(name="load_key", log_file="security.log")
    try:
        path_key = Path(path_key)

        if path_key.exists():
            key = path_key.read_bytes()
        else:
            key = Fernet.generate_key()
            path_key.parent.mkdir(parents=True, exist_ok=True)
            path_key.write_bytes(key)

        logger.info("Secret key loaded")
        return key

    except Exception as ex:
        logger.exception(ex)


class SecurityManager:
    def __init__(self):
        self.logger_name = "SecurityManager"
        self.key = load_key(config_key["key"]["secret_key"])
        self.cipher = Fernet(self.key)

    async def encrypt(self, value: str) -> str:
        logger = logger_config(name=f"{self.logger_name}_encrypt", log_file="security.log")
        try:
            encrypted = self.cipher.encrypt(value.encode("utf-8"))
            return encrypted.decode("utf-8")
        except Exception as ex:
            logger.exception(ex)
            return None

    async def decrypt(self, encrypted_value: str) -> str:
        logger = logger_config(name=f"{self.logger_name}_decrypt", log_file="security.log")
        try:
            decrypted = self.cipher.decrypt(encrypted_value.encode("utf-8"))
            return decrypted.decode("utf-8")
        except Exception as ex:
            logger.exception(ex)
            return None

    async def verify(self, value: str, encrypted_value: str) -> bool:
        logger = logger_config(name=f"{self.logger_name}_verify", log_file="security.log")
        try:
            decrypted = await self.decrypt(encrypted_value)
            return decrypted == value
        except Exception as ex:
            logger.exception(ex)
            return False

    async def generate_password(self, length: int = 12) -> str:
        logger = logger_config(name=f"{self.logger_name}_generate_password", log_file="security.log")
        try:
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
            password = "".join(secrets.choice(alphabet) for _ in range(length))
            return password
        except Exception as ex:
            logger.exception(ex)
            return None

    def generate_session_token(self, lifetime_hours: int = 12):
        logger = logger_config(name="generate_session_token", log_file="SessionUserToken.log")

        try:
            raw = secrets.token_hex(32)

            signature = hmac.new(
                key=self.key,
                msg=raw.encode(),
                digestmod=hashlib.sha256
            ).hexdigest()

            token = f"{raw}.{signature}"
            expires_at = datetime.now(timezone.utc) + timedelta(hours=lifetime_hours)

            return {
                "status": True,
                "token": token,
                "raw": raw,
                "expires_at": expires_at
            }

        except Exception as ex:
            logger.exception(f"Failed to generate session token: {ex}")
            return {"status": False, "message": "Failed to generate session token"}