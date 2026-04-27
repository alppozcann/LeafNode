import asyncio
import logging
from datetime import datetime, timezone, timedelta

from app.database import AsyncSessionLocal
from app.models.sensor_reading import SensorReading
from app.influx_client import InfluxDBManager
from app.services.anomaly_detection import run_anomaly_detection

logger = logging.getLogger(__name__)

async def influx_listener():
    """Continuously poll InfluxDB for new readings and run anomaly detection."""
    poll_interval = 10
    logger.info("Initializing InfluxDB polling listener...")
    last_check_time = datetime.now(timezone.utc) - timedelta(seconds=poll_interval)

    while True:
        await asyncio.sleep(poll_interval)

        # Fetch from InfluxDB — keep last_check_time unchanged on failure so we
        # retry the same window rather than silently skipping it.
        try:
            now = datetime.now(timezone.utc)
            readings_data = await InfluxDBManager.query_recent_readings(last_check_time)
        except asyncio.CancelledError:
            logger.info("Influx listener cancelled — shutting down")
            break
        except Exception as e:
            logger.exception("InfluxDB query failed, will retry next cycle: %s", e)
            continue

        # Advance checkpoint only after a successful fetch so that a failed DB
        # write doesn't skip the window — losing a reading is acceptable, but
        # duplicating it (from re-fetching the same window) is not.
        last_check_time = now

        for data in readings_data:
            try:
                async with AsyncSessionLocal() as db:
                    reading = SensorReading(
                        device_id=data["device_id"],
                        wake_count=data["wake_count"],
                        temperature=data["temperature"],
                        humidity=data["humidity"],
                        pressure=data["pressure"],
                        light=min(float(data["light"]), 1000.0),
                        soil_moisture=data.get("soil_moisture", 0.0),
                        timestamp=data["timestamp"]
                    )
                    db.add(reading)
                    await db.commit()
                    await db.refresh(reading)

                    logger.info(
                        "Polled new reading id=%d for device=%s from InfluxDB",
                        reading.id,
                        reading.device_id,
                    )

                    await run_anomaly_detection(db, reading)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(
                    "Failed to process reading for device=%s: %s",
                    data.get("device_id", "unknown"), e
                )
