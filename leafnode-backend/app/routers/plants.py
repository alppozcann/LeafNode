import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.plant_profile import PlantProfile
from app.schemas.plant_profile import PlantProfileCreate, PlantProfileOut
from app.services.llm_threshold import ThresholdGenerationError, generate_thresholds

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plants", tags=["plants"])


@router.post("", response_model=PlantProfileOut, status_code=status.HTTP_201_CREATED)
async def create_plant(body: PlantProfileCreate, db: AsyncSession = Depends(get_db)):
    """Register a plant profile for a device. Replaces any existing profile."""
    try:
        thresholds = await generate_thresholds(body.plant_name)
    except ThresholdGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM threshold generation failed: {exc}",
        )

    # Upsert: delete existing profile for this device if present
    result = await db.execute(
        select(PlantProfile).where(PlantProfile.device_id == body.device_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        await db.delete(existing)
        await db.flush()

    profile = PlantProfile(
        plant_name=body.plant_name,
        device_id=body.device_id,
        temperature_min=thresholds["temperature"]["min"],
        temperature_max=thresholds["temperature"]["max"],
        humidity_min=thresholds["humidity"]["min"],
        humidity_max=thresholds["humidity"]["max"],
        pressure_min=thresholds["pressure"]["min"],
        pressure_max=thresholds["pressure"]["max"],
        light_min=thresholds["light"]["min"],
        light_max=thresholds["light"]["max"],
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    logger.info("Created plant profile id=%d for device=%s", profile.id, profile.device_id)
    return profile


@router.get("/{device_id}", response_model=PlantProfileOut)
async def get_plant(device_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PlantProfile).where(PlantProfile.device_id == device_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No plant profile found for device '{device_id}'",
        )
    return profile
