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
    timestamp: datetime
