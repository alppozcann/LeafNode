from fastapi import APIRouter, HTTPException, Query, Path, status

from app.influx_client import InfluxDBManager
from app.schemas.sensor_reading import SensorReadingOut

router = APIRouter(prefix="/readings", tags=["readings"])


@router.get("/{device_id}", response_model=list[SensorReadingOut])
async def get_readings(
    device_id: str = Path(..., pattern=r"^[a-zA-Z0-9_\-]+$"),
    range: str = Query(default="3h", pattern=r"^[0-9]+[hdm]$"),
):
    return await InfluxDBManager.query_sensor_readings(device_id, time_range=range)


@router.get("/{device_id}/latest", response_model=SensorReadingOut)
async def get_latest_reading(device_id: str = Path(..., pattern=r"^[a-zA-Z0-9_\-]+$")):
    readings = await InfluxDBManager.query_sensor_readings(device_id, limit=1)
    if not readings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No readings found for device '{device_id}'",
        )
    return readings[0]
