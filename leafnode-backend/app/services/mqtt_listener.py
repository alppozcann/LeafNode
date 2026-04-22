import asyncio
import json
import logging
from datetime import datetime, timezone
import aiomqtt
from sqlalchemy import select, update
from app.config import settings
from app.database import AsyncSessionLocal
from app.models.command_queue import CommandQueue, CommandStatus

logger = logging.getLogger(__name__)


async def _process_status_message(device_id: str, payload_str: str, mqtt_client: aiomqtt.Client):
    """If device is online, send all pending commands from the queue."""
    if payload_str.lower() != "online":
        return

    logger.info("Device %s is online. Checking for pending commands...", device_id)
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(CommandQueue)
            .where(CommandQueue.device_id == device_id)
            .where(CommandQueue.status == CommandStatus.PENDING)
            .order_by(CommandQueue.created_at.asc())
        )
        pending_commands = result.scalars().all()

        if not pending_commands:
            logger.info("No pending commands for device %s", device_id)
            return

        for cmd in pending_commands:
            topic = f"group1/{device_id}/cmd"
            payload = {"cmd": cmd.cmd}
            if cmd.params:
                payload.update(cmd.params)
            
            try:
                await mqtt_client.publish(topic, payload=json.dumps(payload), qos=1)
                
                # Update status to SENT
                cmd.status = CommandStatus.SENT
                cmd.sent_at = datetime.now(timezone.utc)
                await db.commit()
                logger.info("Sent queued command %s (id=%d) to %s", cmd.cmd, cmd.id, topic)
            except Exception as e:
                logger.error("Failed to send queued command %d: %s", cmd.id, e)


async def _process_ack_message(device_id: str, payload_str: str):
    """Update the most recent 'SENT' command for this device to 'ACKED'."""
    try:
        data = json.loads(payload_str)
        ack_cmd = data.get("ack")
        if not ack_cmd:
            return

        async with AsyncSessionLocal() as db:
            # Find the latest SENT command for this device with matching command name
            result = await db.execute(
                select(CommandQueue)
                .where(CommandQueue.device_id == device_id)
                .where(CommandQueue.status == CommandStatus.SENT)
                .where(CommandQueue.cmd == ack_cmd)
                .order_by(CommandQueue.sent_at.desc())
                .limit(1)
            )
            cmd = result.scalar_one_or_none()

            if cmd:
                cmd.status = CommandStatus.ACKED
                cmd.acked_at = datetime.now(timezone.utc)
                await db.commit()
                logger.info("Command %s (id=%d) for %s marked as ACKED", cmd.cmd, cmd.id, device_id)
            else:
                logger.warning("Received ACK for %s but no matching SENT command found in queue", ack_cmd)
    except Exception as e:
        logger.error("Error processing ACK for %s: %s", device_id, e)


async def mqtt_ack_listener():
    """Continuously listen for telemetry, status and acknowledgments from all devices."""
    # CORRECTED: Wildcards must occupy a full level (+ or #)
    topics = [
        "group1/+",                    # Listen to all devices main telemetry
        "group1/+/status",              # Status updates
        "group1/+/ack"                 # Command acknowledgments
    ]
    logger.info("Initializing MQTT Command Queue listener on topics: %s", topics)
    
    while True:
        try:
            async with aiomqtt.Client(
                hostname=settings.MQTT_BROKER,
                port=settings.MQTT_PORT,
                username=settings.MQTT_USER,
                password=settings.MQTT_PASS
            ) as client:
                for topic in topics:
                    await client.subscribe(topic)
                
                async for message in client.messages:
                    topic_str = str(message.topic)
                    topic_parts = topic_str.split("/")
                    
                    if len(topic_parts) < 2:
                        continue

                    device_id = topic_parts[1]
                    
                    # Security/Filter check: Only process leafnode devices
                    if not device_id.startswith("leafnode-"):
                        continue
                    
                    if len(topic_parts) == 2:
                        # Telemetry received -> Device is awake!
                        await _process_status_message(device_id, "online", client)
                    
                    elif len(topic_parts) == 3:
                        category = topic_parts[2]
                        payload_str = message.payload.decode()

                        if category == "status":
                            await _process_status_message(device_id, payload_str, client)
                        elif category == "ack":
                            await _process_ack_message(device_id, payload_str)

        except aiomqtt.MqttError as error:
            logger.error("MQTT connection error: %s. Reconnecting in 5 seconds...", error)
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            logger.info("MQTT Command Queue listener cancelled — shutting down")
            break
        except Exception as e:
            logger.exception("Unexpected error in MQTT listener: %s", e)
            await asyncio.sleep(5)
