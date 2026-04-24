from datetime import datetime
from pydantic import BaseModel
from app.models.command_queue import CommandStatus


class CommandCreate(BaseModel):
    cmd: str
    params: dict | None = None


class CommandOut(BaseModel):
    id: int
    device_id: str
    cmd: str
    params: dict | None
    status: CommandStatus
    created_at: datetime
    sent_at: datetime | None
    acked_at: datetime | None

    class Config:
        from_attributes = True
