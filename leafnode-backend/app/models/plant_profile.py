from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PlantProfile(Base):
    __tablename__ = "plant_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    plant_name: Mapped[str] = mapped_column(String, nullable=False)
    device_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    temperature_min: Mapped[float] = mapped_column(Float, nullable=False)
    temperature_max: Mapped[float] = mapped_column(Float, nullable=False)
    humidity_min: Mapped[float] = mapped_column(Float, nullable=False)
    humidity_max: Mapped[float] = mapped_column(Float, nullable=False)
    pressure_min: Mapped[float] = mapped_column(Float, nullable=False)
    pressure_max: Mapped[float] = mapped_column(Float, nullable=False)
    light_min: Mapped[float] = mapped_column(Float, nullable=False)
    light_max: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
