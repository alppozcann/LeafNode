import asyncio
import json
import logging

import asyncio_mqtt as mqtt
from pydantic import ValidationError

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.sensor_reading import SensorReading
from app.schemas.sensor_reading import SensorReadingIncoming
from app.services.anomaly_detection import run_anomaly_detection

logger = logging.getLogger(__name__)


async def _handle_message(payload: bytes) -> None:
    """Validate, persist, and run anomaly detection for a single MQTT message."""
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError:
        logger.warning("Received non-JSON MQTT payload: %r", payload)
        return

    try:
        incoming = SensorReadingIncoming.model_validate(raw)
    except ValidationError as exc:
        logger.warning("Invalid sensor payload: %s | raw=%s", exc, raw)
        return

    async with AsyncSessionLocal() as db:
        reading = SensorReading(
            device_id=incoming.device_id,
            wake_count=incoming.wake_count,
            temperature=incoming.temperature,
            humidity=incoming.humidity,
            pressure=incoming.pressure,
            light=incoming.light,
        )
        db.add(reading)
        await db.commit()
        await db.refresh(reading)

        logger.info(
            "Stored reading id=%d for device=%s (wake_count=%d)",
            reading.id,
            reading.device_id,
            reading.wake_count,
        )

        await run_anomaly_detection(db, reading)


async def mqtt_listener() -> None:
    """Connect to the MQTT broker and listen for sensor messages indefinitely.

    Reconnects automatically on connection loss.
    """
    reconnect_delay = 5

    while True:
        try:
            async with mqtt.Client(
                hostname=settings.MQTT_BROKER_HOST,
                port=settings.MQTT_BROKER_PORT,
            ) as client:
                logger.info(
                    "MQTT connected to %s:%d — subscribing to '%s'",
                    settings.MQTT_BROKER_HOST,
                    settings.MQTT_BROKER_PORT,
                    settings.MQTT_TOPIC,
                )
                await client.subscribe(settings.MQTT_TOPIC)

                async with client.messages() as messages:
                    async for message in messages:
                        try:
                            await _handle_message(message.payload)
                        except Exception:
                            logger.exception("Unhandled error processing MQTT message")

        except mqtt.MqttError as exc:
            logger.error(
                "MQTT connection error: %s — retrying in %ds", exc, reconnect_delay
            )
            await asyncio.sleep(reconnect_delay)
        except asyncio.CancelledError:
            logger.info("MQTT listener cancelled — shutting down")
            break
        except Exception:
            logger.exception("Unexpected MQTT error — retrying in %ds", reconnect_delay)
            await asyncio.sleep(reconnect_delay)
