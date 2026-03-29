from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.sensor_reading import SensorReading
from app.schemas.sensor_reading import SensorReadingOut

router = APIRouter(prefix="/readings", tags=["readings"])


@router.get("/{device_id}", response_model=list[SensorReadingOut])
async def get_readings(
    device_id: str,
    limit: int = Query(default=50, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SensorReading)
        .where(SensorReading.device_id == device_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{device_id}/latest", response_model=SensorReadingOut)
async def get_latest_reading(device_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SensorReading)
        .where(SensorReading.device_id == device_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(1)
    )
    reading = result.scalar_one_or_none()
    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No readings found for device '{device_id}'",
        )
    return reading
