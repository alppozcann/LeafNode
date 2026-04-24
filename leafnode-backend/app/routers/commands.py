import logging
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.command_queue import CommandQueue, CommandStatus
from app.schemas.command_queue import CommandCreate, CommandOut

import aiomqtt
import json
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/devices", tags=["commands"])


@router.post("/{device_id}/command", status_code=status.HTTP_201_CREATED)
async def queue_command(
    device_id: str, payload: CommandCreate, db: AsyncSession = Depends(get_db)
):
    """Queue a command AND publish it immediately just in case the device is awake."""
    new_cmd = CommandQueue(
        device_id=device_id,
        cmd=payload.cmd,
        params=payload.params,
        status=CommandStatus.PENDING,
    )
    db.add(new_cmd)
    await db.commit()
    await db.refresh(new_cmd)

    # 1. Publish immediately
    topic = f"group1/{device_id}/cmd"
    mqtt_payload = {"cmd": payload.cmd}
    if payload.params:
        mqtt_payload.update(payload.params)
    
    try:
        async with aiomqtt.Client(
            hostname=settings.MQTT_BROKER,
            port=settings.MQTT_PORT,
            username=settings.MQTT_USER,
            password=settings.MQTT_PASS
        ) as client:
            await client.publish(topic, payload=json.dumps(mqtt_payload), qos=1)
            logger.info("Published immediate command %s to %s", payload.cmd, topic)
            
            # Since we just sent it, we can mark it as SENT (but not ACKED yet)
            new_cmd.status = CommandStatus.SENT
            new_cmd.sent_at = datetime.now(timezone.utc)
            await db.commit()
            
    except Exception as e:
        logger.warning("Immediate MQTT publish failed (device likely asleep): %s", e)
        # We don't raise an error here because the background listener will retry when device wakes up

    return {
        "queued": True,
        "command_id": new_cmd.id,
        "status": new_cmd.status,
    }


@router.get("/{device_id}/commands", response_model=List[CommandOut])
async def get_commands(
    device_id: str, limit: int = 20, db: AsyncSession = Depends(get_db)
):
    """Get the command history for a specific device."""
    result = await db.execute(
        select(CommandQueue)
        .where(CommandQueue.device_id == device_id)
        .order_by(CommandQueue.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
