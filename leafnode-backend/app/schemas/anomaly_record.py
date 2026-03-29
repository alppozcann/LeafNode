from datetime import datetime

from pydantic import BaseModel


class AnomalyRecordOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    device_id: str
    sensor_reading_id: int
    metric: str
    value: float
    expected_min: float | None
    expected_max: float | None
    rule_type: str
    explanation: str | None
    timestamp: datetime
