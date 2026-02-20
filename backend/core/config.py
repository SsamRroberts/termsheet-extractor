from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings

_BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    POSTGRES_HOST: str = "localhost"
    POSTGRES_DB: str = "bluebridge"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_PORT: int = 5432
    ENVIRONMENT: str = "development"
    LOG_PATH: str | None = None
    ALLOWED_ORIGINS: str | list[str] = ["*"]

    BLOBSTORE_PATH: str = "./blobstore"

    # LLM settings (OpenAI-compatible API)
    LLM_API_KEY: str
    LLM_MODEL: str = "gpt-4o"
    LLM_API_URL: str | None = None

    class Config:
        env_file = str(_BACKEND_DIR / ".env")

    @field_validator("ALLOWED_ORIGINS", mode="before")
    def parse_allowed_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @property
    def DATABASE_URL(self) -> str:
        host = self.POSTGRES_HOST.split(":")[0] if ":" in self.POSTGRES_HOST else self.POSTGRES_HOST
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{host}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def LOG_FILE(self) -> str | None:
        return (self.LOG_PATH + "/bluebridge.log") if self.LOG_PATH else None


settings = Settings()  # type: ignore
