import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import aiomqtt
import json
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/devices", tags=["commands"])

class CommandPayload(BaseModel):
    cmd: str
    times: int | None = None

@router.post("/{device_id}/command", status_code=status.HTTP_200_OK)
async def send_command(device_id: str, payload: CommandPayload):
    topic = f"group1/{device_id}/cmd"
    message = payload.model_dump(exclude_none=True)
    
    try:
        async with aiomqtt.Client(
            hostname=settings.MQTT_BROKER,
            port=settings.MQTT_PORT,
            username=settings.MQTT_USER,
            password=settings.MQTT_PASS
        ) as client:
            await client.publish(topic, payload=json.dumps(message), qos=1)
            logger.info("Published command %s to %s", message, topic)
    except Exception as e:
        logger.error("Failed to publish MQTT command: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send command to device broker"
        )
    
    return {
        "status": "command queued", 
        "command": payload.cmd, 
        "note": "Command will be executed during the next 35s wake window"
    }
