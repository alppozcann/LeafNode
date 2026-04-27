import logging
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.command_queue import CommandQueue, CommandStatus
from app.schemas.command_queue import CommandCreate, CommandOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/devices", tags=["commands"])


@router.post("/{device_id}/command", status_code=status.HTTP_201_CREATED)
async def queue_command(
    device_id: str, payload: CommandCreate, db: AsyncSession = Depends(get_db)
):
    """Queue a command. The MQTT listener publishes it on the next status=online from the device."""
    new_cmd = CommandQueue(
        device_id=device_id,
        cmd=payload.cmd,
        params=payload.params,
        status=CommandStatus.PENDING,
    )
    db.add(new_cmd)
    await db.commit()
    await db.refresh(new_cmd)

    logger.info("Queued command %s (id=%d) for %s — will publish on next wake", payload.cmd, new_cmd.id, device_id)

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
