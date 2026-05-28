from config import config_database
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

engine = create_async_engine(
    config_database["database_url"].format(**config_database["database"]),
    echo=False,
    future=True,
    pool_size=15,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=60,
    connect_args={"server_settings": {"application_name": "SocialMetrics"}}
)

SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

def get_session():
    return SessionLocal()