import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.jwt_utils import decode_token, hash_jti, make_access_token, make_refresh_token
from app.auth.models import RefreshToken, User
from app.auth.password import hash_password, verify_password
from app.auth.rate_limiter import login_limiter
from app.auth.schemas import ChangePasswordRequest, LoginRequest, UserOut
from app.config import settings
from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

_COOKIE_OPTS: dict = {"httponly": True, "samesite": "strict", "secure": not settings.DEBUG}


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie("access_token", access_token, max_age=15 * 60, **_COOKIE_OPTS)
    response.set_cookie("refresh_token", refresh_token, max_age=7 * 24 * 3600, **_COOKIE_OPTS)


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", httponly=True, samesite="strict")
    response.delete_cookie("refresh_token", httponly=True, samesite="strict")


@router.post("/login")
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    ip = request.headers.get("X-Forwarded-For", request.client.host or "").split(",")[0].strip()
    if not await login_limiter.check(ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again in 15 minutes.",
        )

    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        logger.warning("Failed login for username=%r from ip=%s", body.username, ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    await login_limiter.reset(ip)
    access_token = make_access_token(user.id, user.username, settings.JWT_SECRET)
    refresh_token_str, jti = make_refresh_token(user.id, user.username, settings.JWT_SECRET)
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_jti(jti),
        expires_at=datetime.fromtimestamp(time.time() + 7 * 24 * 3600, tz=timezone.utc),
    ))
    await db.commit()
    _set_auth_cookies(response, access_token, refresh_token_str)
    logger.info("User %r logged in from ip=%s", user.username, ip)
    return {"username": user.username}


@router.post("/refresh")
async def refresh_tokens(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    if not refresh_token:
        raise exc
    try:
        payload = decode_token(refresh_token, settings.JWT_SECRET)
    except ValueError:
        raise exc
    if payload.get("type") != "refresh":
        raise exc

    jti = payload.get("jti", "")
    user_id = int(payload["sub"])
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_jti(jti),
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,  # noqa: E712
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        _clear_auth_cookies(response)
        raise exc

    record.revoked = True
    await db.flush()
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        await db.commit()
        raise exc

    new_access = make_access_token(user.id, user.username, settings.JWT_SECRET)
    new_refresh_str, new_jti = make_refresh_token(user.id, user.username, settings.JWT_SECRET)
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_jti(new_jti),
        expires_at=datetime.fromtimestamp(time.time() + 7 * 24 * 3600, tz=timezone.utc),
    ))
    await db.commit()
    _set_auth_cookies(response, new_access, new_refresh_str)
    return {"ok": True}


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    if refresh_token:
        try:
            payload = decode_token(refresh_token, settings.JWT_SECRET)
            jti = payload.get("jti", "")
            if jti:
                await db.execute(delete(RefreshToken).where(RefreshToken.token_hash == hash_jti(jti)))
                await db.commit()
        except ValueError:
            pass
    _clear_auth_cookies(response)
    return {"ok": True}


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    user.password_hash = hash_password(body.new_password)
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    await db.commit()
    _clear_auth_cookies(response)
    logger.info("Password changed for user %r — all sessions invalidated", user.username)
    return {"ok": True}


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
