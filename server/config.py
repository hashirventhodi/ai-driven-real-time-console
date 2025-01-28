# server/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Platform DB
    PLATFORM_DB_HOST: str = os.getenv("PLATFORM_DB_HOST", "localhost")
    PLATFORM_DB_PORT: int = int(os.getenv("PLATFORM_DB_PORT", 5432))
    PLATFORM_DB_USER: str = os.getenv("PLATFORM_DB_USER", "")
    PLATFORM_DB_PASSWORD: str = os.getenv("PLATFORM_DB_PASSWORD", "")
    PLATFORM_DB_NAME: str = os.getenv("PLATFORM_DB_NAME", "")

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", None)

    # OpenAI (if used)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")

settings = Settings()
