from datetime import datetime

from pydantic import BaseModel


class PlantProfileCreate(BaseModel):
    plant_name: str
    device_id: str


class PlantProfileOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    plant_name: str
    device_id: str
    temperature_min: float
    temperature_max: float
    humidity_min: float
    humidity_max: float
    pressure_min: float
    pressure_max: float
    light_min: float
    light_max: float
    created_at: datetime
