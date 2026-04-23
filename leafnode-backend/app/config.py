from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    
    # InfluxDB configurations
    INFLUXDB_URL: str
    INFLUXDB_USERNAME: str = ""
    INFLUXDB_PASSWORD: str = ""
    INFLUXDB_ORG: str
    INFLUXDB_BUCKET: str
    INFLUXDB_MEASUREMENT: str = "sensor_reading"

    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    
    TREND_DELTA_TEMPERATURE: float = 3.0
    TREND_DELTA_HUMIDITY: float = 10.0
    TREND_DELTA_LIGHT: float = 500.0
    TREND_DELTA_PRESSURE: float = 5.0
    TREND_DELTA_SOIL_MOISTURE: float = 15.0
    
    # Fallback model list for LLM explanation
    GEMINI_FALLBACK_MODELS: list[str] = [
        "gemini-3.1-pro",
        "gemini-3.1-flash-lite",
        "gemini-3-flash",
        "gemini-3-flash-live",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite"
    ]

    # MQTT configuration
    MQTT_BROKER: str
    MQTT_PORT: int = 1883
    MQTT_USER: str = ""
    MQTT_PASS: str = ""


settings = Settings()
