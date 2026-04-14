from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NutriFlow AI API"
    app_version: str = "0.1.0"
    debug: bool = True
    database_url: str = "sqlite:///./nutriflow.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()