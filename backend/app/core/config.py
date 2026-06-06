from functools import lru_cache
from pathlib import Path
import platform

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_data_dir(system_name: str | None = None) -> Path:
    system = (system_name or platform.system()).lower()
    if system.startswith("win"):
        return Path("C:/Users/Administrator/OneDrive/ASELF/Data/PaperInsight/")
    if system == "linux":
        return Path("/home/jj/OneDrive/ASELF/Data/PaperInsight/")
    return Path("/Users/johnjim/Library/CloudStorage/OneDrive-个人/ASELF/Data/PaperInsight/")


class Settings(BaseSettings):
    database_url: str = "sqlite:///./paper_insight.db"
    data_dir: Path = Field(default_factory=default_data_dir)
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4.1-mini"
    semantic_scholar_api_key: str | None = None
    feishu_app_id: str | None = None
    feishu_app_secret: str | None = None
    feishu_recipient_id: str | None = None
    feishu_recipient_id_type: str = Field(default="email", pattern="^(email|open_id|user_id)$")

    @field_validator("data_dir", mode="before")
    @classmethod
    def use_default_data_dir_for_empty_value(cls, value):
        if value is None or str(value).strip() == "":
            return default_data_dir()
        return value

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
