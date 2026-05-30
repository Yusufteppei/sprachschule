from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Sprachschule"
    DEBUG: bool = False
    
    # API Keys (No default values = Required)
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str | None = None
    
    # Database
    DATABASE_URL: str
    
    # Configuration for Pydantic
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8"
    )

@lru_cache
def get_settings():
    """
    Returns a cached instance of the settings.
    Using lru_cache ensures we only read the .env once.
    """
    return Settings()

settings = get_settings()