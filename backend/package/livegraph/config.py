from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_dsn: str = "postgresql+asyncpg://livegraph:livegraph_dev_password@postgres:5432/livegraph"
    redis_url:str= "redis://redis:6379"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    embed_model: str = "all-minilm"
    embed_base_url: str = "http://ollama:11434/v1/embeddings"
    embed_api_key: str = "ollama"
    embed_dimension: int = 384
    milvus_uri: str = "http://milvus:19530"
    milvus_token: str = ""

settings = Settings()