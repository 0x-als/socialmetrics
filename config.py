import os

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
base_dir = Path(__file__).resolve().parent

config_database = {
    "database": {
        "user": os.getenv("DATABASE_USER"),
        "host": os.getenv("DATABASE_HOST"),
        "port": os.getenv("DATABASE_PORT"),
        "database": os.getenv("DATABASE_NAME"),
        "password": os.getenv("DATABASE_PASSWORD"),
    },
    "database_url": "postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
}

config_key = {
    "key": {
        "secret_key": base_dir / os.getenv("SECRET_KEY")
    }
}

config_telegram = {
    "telethon": {
        "system_version": "4.16.30-vxCUSTOM",
        "device_model": "CustomDevice",
        "app_version": "1.0.0",
    }
}
