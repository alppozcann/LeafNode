from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.anomaly_record import AnomalyRecord
from app.schemas.anomaly_record import AnomalyRecordOut

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("/{device_id}", response_model=list[AnomalyRecordOut])
async def get_anomalies(
    device_id: str,
    limit: int = Query(default=50, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AnomalyRecord)
        .where(AnomalyRecord.device_id == device_id)
        .order_by(AnomalyRecord.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{device_id}/latest", response_model=AnomalyRecordOut)
async def get_latest_anomaly(device_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AnomalyRecord)
        .where(AnomalyRecord.device_id == device_id)
        .order_by(AnomalyRecord.timestamp.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No anomaly records found for device '{device_id}'",
        )
    return record
