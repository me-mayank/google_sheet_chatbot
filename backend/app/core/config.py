from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    GROQ_API_KEY: str
    GOOGLE_DOC_URL: str
    MODEL_NAME: str = "llama-3.3-70b-versatile"
    MODEL_PROVIDER: str = "groq"
    ALLOWED_ORIGINS: str = "*"
    DOCUMENT_CACHE_TTL_SECONDS: int = 300
    DEFAULT_CONTEXT_ID: str = "icpc_default"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
