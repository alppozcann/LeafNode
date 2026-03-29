from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "postgresql+asyncpg://leafnode_user:KingoBabayaSelam1@localhost:5432/leafnode"
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_TOPIC: str = "leafnode/sensors"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    TREND_DELTA_TEMPERATURE: float = 3.0
    TREND_DELTA_HUMIDITY: float = 10.0
    TREND_DELTA_LIGHT: float = 500.0
    TREND_DELTA_PRESSURE: float = 5.0


settings = Settings()
