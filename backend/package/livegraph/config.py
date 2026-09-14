from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_dsn: str = "postgresql+asyncpg://livegraph:livegraph_dev_password@postgres:5432/livegraph"

settings = Settings()