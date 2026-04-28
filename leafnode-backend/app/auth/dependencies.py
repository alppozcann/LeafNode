from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_utils import decode_token
from app.auth.models import User
from app.config import settings
from app.database import get_db

_UNAUTH = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not access_token:
        raise _UNAUTH

    try:
        payload = decode_token(access_token, settings.JWT_SECRET)
    except ValueError:
        raise _UNAUTH

    if payload.get("type") != "access":
        raise _UNAUTH

    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user:
        raise _UNAUTH
    return user
