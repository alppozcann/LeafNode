import asyncio
import logging
import aiomqtt
from app.config import settings

logger = logging.getLogger(__name__)

async def mqtt_ack_listener():
    """Continuously listen for command acknowledgments from all devices."""
    topic = "group1/+/ack"
    logger.info("Initializing MQTT ACK listener on topic %s", topic)
    
    while True:
        try:
            async with aiomqtt.Client(
                hostname=settings.MQTT_BROKER,
                port=settings.MQTT_PORT,
                username=settings.MQTT_USER,
                password=settings.MQTT_PASS
            ) as client:
                await client.subscribe(topic)
                async for message in client.messages:
                    payload = message.payload.decode()
                    logger.info("[MQTT ACK] %s: %s", message.topic, payload)
        except aiomqtt.MqttError as error:
            logger.error("MQTT connection error: %s. Reconnecting in 5 seconds...", error)
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            logger.info("MQTT ACK listener cancelled — shutting down")
            break
        except Exception as e:
            logger.exception("Unexpected error in MQTT ACK listener: %s", e)
            await asyncio.sleep(5)
