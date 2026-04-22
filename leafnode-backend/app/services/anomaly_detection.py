import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.anomaly_record import AnomalyRecord
from app.models.plant_profile import PlantProfile
from app.models.sensor_reading import SensorReading
from app.services.llm_explanation import generate_explanation

logger = logging.getLogger(__name__)

# Maps metric name → (profile min attr, profile max attr, trend delta setting)
METRICS = {
    "temperature": ("temperature_min", "temperature_max", settings.TREND_DELTA_TEMPERATURE),
    "humidity": ("humidity_min", "humidity_max", settings.TREND_DELTA_HUMIDITY),
    "pressure": ("pressure_min", "pressure_max", settings.TREND_DELTA_PRESSURE),
    "light": ("light_min", "light_max", settings.TREND_DELTA_LIGHT),
    "soil_moisture": ("soil_moisture_min", "soil_moisture_max", settings.TREND_DELTA_SOIL_MOISTURE),
}


def _get_metric_value(reading: SensorReading, metric: str) -> float:
    return getattr(reading, metric)


async def _load_profile(db: AsyncSession, device_id: str) -> PlantProfile | None:
    result = await db.execute(
        select(PlantProfile).where(PlantProfile.device_id == device_id)
    )
    return result.scalar_one_or_none()


async def _load_recent_readings(
    db: AsyncSession, device_id: str, limit: int = 3
) -> list[SensorReading]:
    result = await db.execute(
        select(SensorReading)
        .where(SensorReading.device_id == device_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return list(reversed(rows))  # oldest → newest


def _check_thresholds(
    reading: SensorReading, profile: PlantProfile
) -> list[dict]:
    anomalies = []
    for metric, (min_attr, max_attr, _) in METRICS.items():
        value = _get_metric_value(reading, metric)
        exp_min = getattr(profile, min_attr)
        exp_max = getattr(profile, max_attr)
        if value < exp_min or value > exp_max:
            anomalies.append(
                {
                    "metric": metric,
                    "value": value,
                    "expected_min": exp_min,
                    "expected_max": exp_max,
                    "rule_type": "threshold",
                }
            )
    return anomalies


def _check_trends(readings: list[SensorReading]) -> list[dict]:
    """Detect monotonically increasing or decreasing trends across the last N readings.

    A trend anomaly is raised when the total change across readings exceeds the
    configured delta for that metric.
    """
    if len(readings) < 3:
        return []

    anomalies = []
    for metric, (_, _, delta) in METRICS.items():
        values = [_get_metric_value(r, metric) for r in readings]

        increasing = all(values[i] < values[i + 1] for i in range(len(values) - 1))
        decreasing = all(values[i] > values[i + 1] for i in range(len(values) - 1))

        total_change = abs(values[-1] - values[0])

        if (increasing or decreasing) and total_change > delta:
            anomalies.append(
                {
                    "metric": metric,
                    "value": values[-1],
                    "expected_min": None,
                    "expected_max": None,
                    "rule_type": "trend",
                }
            )
    return anomalies


async def run_anomaly_detection(
    db: AsyncSession, reading: SensorReading
) -> list[AnomalyRecord]:
    """Run threshold + trend anomaly detection for a new sensor reading.

    Stores all found anomalies, then calls the LLM explanation service once
    if any anomalies were found. Returns the stored AnomalyRecord list.
    """
    profile = await _load_profile(db, reading.device_id)
    if profile is None:
        logger.info(
            "No plant profile for device %s — skipping anomaly detection", reading.device_id
        )
        return []

    # Load recent readings INCLUDING the current one for trend analysis
    recent = await _load_recent_readings(db, reading.device_id, limit=3)

    anomaly_dicts = _check_thresholds(reading, profile)
    anomaly_dicts.extend(_check_trends(recent))

    if not anomaly_dicts:
        return []

    now = datetime.now(timezone.utc)
    records = [
        AnomalyRecord(
            device_id=reading.device_id,
            sensor_reading_id=reading.id,
            timestamp=now,
            **a,
        )
        for a in anomaly_dicts
    ]

    db.add_all(records)
    await db.flush()  # get IDs before explanation call

    # LLM explanation — a single call describes all anomalies together
    explanation = await generate_explanation(
        plant_name=profile.plant_name,
        current_reading=reading,
        anomalies=records,
        recent_readings=recent,
        soil_moisture=reading.soil_moisture if hasattr(reading, "soil_moisture") else 0,
    )

    if explanation:
        for record in records:
            record.explanation = explanation

    await db.commit()
    for record in records:
        await db.refresh(record)

    logger.info(
        "Stored %d anomaly record(s) for device %s (reading id=%d)",
        len(records),
        reading.device_id,
        reading.id,
    )
    return records
