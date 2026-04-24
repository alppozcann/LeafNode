from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import JSON, DateTime, Integer, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CommandStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    ACKED = "acked"


class CommandQueue(Base):
    __tablename__ = "command_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String, index=True)
    cmd: Mapped[str] = mapped_column(String)
    params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[CommandStatus] = mapped_column(
        SQLEnum(CommandStatus), default=CommandStatus.PENDING, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
