from datetime import datetime

from pydantic import BaseModel, Field


class SensorReadingIncoming(BaseModel):
    device_id: str
    wake_count: int
    temperature: float
    humidity: float = Field(..., ge=0, le=100)
    pressure: float
    light: float = Field(..., ge=0)


class SensorReadingOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    device_id: str
    wake_count: int
    temperature: float
    humidity: float
    pressure: float
    light: float
    temperature_raw: float | None = None
    humidity_raw: float | None = None
    pressure_raw: float | None = None
    soil_raw: int | None = None
    soil_moisture: int | None = None
    bme_ok: bool | None = None
    soil_ok: bool | None = None
    ldr_ok: bool | None = None
    timestamp: datetime
