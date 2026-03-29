from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AnomalyRecord(Base):
    __tablename__ = "anomaly_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    sensor_reading_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sensor_readings.id"), nullable=False
    )
    metric: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    expected_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    rule_type: Mapped[str] = mapped_column(String, nullable=False)  # "threshold" | "trend"
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
