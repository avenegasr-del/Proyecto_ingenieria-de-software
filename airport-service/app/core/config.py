from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    API_COLOMBIA_URL: str = "https://api-colombia.com/api/v1"
    LOG_LEVEL: str = "INFO"
    APP_TITLE: str = "Airport Service"
    APP_VERSION: str = "1.0.0"
    HTTP_TIMEOUT: float = 10.0


settings = Settings()
