import json
from pydantic import field_validator
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

    GEMINI_API_KEYS: list[str] = []
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"

    @field_validator("GEMINI_API_KEYS", mode="before")
    @classmethod
    def parse_gemini_keys(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("["):
                return json.loads(v)
            return [k.strip() for k in v.split(",") if k.strip()]
        return v
    
    TREND_DELTA_TEMPERATURE: float = 3.0
    TREND_DELTA_HUMIDITY: float = 10.0
    TREND_DELTA_LIGHT: float = 500.0
    TREND_DELTA_PRESSURE: float = 5.0
    TREND_DELTA_SOIL_MOISTURE: float = 15.0
    
    # Fallback model list — ordered by quality then RPD availability.
    # IDs verified via API discovery (supported_actions contains generateContent).
    # Non-text models (tts, image, live, robotics, embedding, veo, etc.) excluded.
    GEMINI_FALLBACK_MODELS: list[str] = [
        # Gemini 3.x series
        "gemini-3.1-pro-preview",        # highest quality; 0 RPD free tier but worth trying
        "gemini-3.1-flash-lite-preview",  # 500 RPD — best RPD among text models
        "gemini-3-pro-preview",
        "gemini-3-flash-preview",         # 20 RPD
        # Gemini 2.5 series
        "gemini-2.5-flash",               # 20 RPD
        "gemini-2.5-pro",                 # 0 RPD free tier; try anyway
        "gemini-2.5-flash-lite",          # 20 RPD (same as primary)
        # Gemini 2.0 series (stable, proven)
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        # Gemma 4 (1.5K RPD, strong quality)
        "gemma-4-31b-it",
        "gemma-4-26b-a4b-it",
        # Gemma 3 large (14.4K RPD — highest availability)
        "gemma-3-27b-it",
        "gemma-3-12b-it",
        "gemma-3n-e4b-it",
        # Gemma 3 small (last resort; may struggle with JSON output format)
        "gemma-3-4b-it",
        "gemma-3n-e2b-it",
        "gemma-3-1b-it",
    ]

    # MQTT configuration
    MQTT_BROKER: str
    MQTT_PORT: int = 1883
    MQTT_USER: str = ""
    MQTT_PASS: str = ""


settings = Settings()
