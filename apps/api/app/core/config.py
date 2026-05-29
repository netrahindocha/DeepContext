from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "DeepContext API"
    environment: str = "local"
    debug: bool = True
    
    model_config = SettingsConfigDict(env_prefix="DEEPCONTEXT_")

@lru_cache
def get_settings() -> Settings:
    return Settings()