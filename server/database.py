# server/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.config import settings

def get_platform_db_url():
    user = settings.PLATFORM_DB_USER
    pwd = settings.PLATFORM_DB_PASSWORD
    host = settings.PLATFORM_DB_HOST
    port = settings.PLATFORM_DB_PORT
    dbname = settings.PLATFORM_DB_NAME
    return f"postgresql://{user}:{pwd}@{host}:{port}/{dbname}"

platform_engine = create_engine(
    get_platform_db_url(),
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)

PlatformSessionLocal = sessionmaker(bind=platform_engine)
