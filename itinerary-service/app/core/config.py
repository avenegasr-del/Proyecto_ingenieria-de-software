from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./itineraries.db"
    AIRPORT_SERVICE_URL: str = "http://localhost:8001"
    LOG_LEVEL: str = "INFO"
    APP_TITLE: str = "Itinerary Service"
    APP_VERSION: str = "1.0.0"
    HTTP_TIMEOUT: float = 10.0


settings = Settings()
