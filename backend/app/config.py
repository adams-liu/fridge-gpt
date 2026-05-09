from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FRIDGE_GPT_")

    token: str = Field(default="dev-token")
    database_url: str = Field(default="sqlite:///./fridge_gpt.db")


@lru_cache
def get_settings() -> Settings:
    return Settings()
