from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str
    gemini_api_key: str
    adzuna_app_id: str
    adzuna_app_key: str
    database_url: str
    redis_url: str
    secret_key: str
    cors_origins: str = "http://localhost:3000"
    max_jobs_per_category: int = 10


settings = Settings()
