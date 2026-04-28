import base64
import hashlib
import hmac
import json
import secrets
import time


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding < 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _sign(message: bytes, secret: str) -> str:
    return _b64_encode(hmac.new(secret.encode(), message, hashlib.sha256).digest())


def create_token(payload: dict, secret: str) -> str:
    header = _b64_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64_encode(json.dumps(payload).encode())
    message = f"{header}.{body}".encode()
    return f"{header}.{body}.{_sign(message, secret)}"


def decode_token(token: str, secret: str) -> dict:
    try:
        header_b64, body_b64, sig_b64 = token.split(".")
    except ValueError:
        raise ValueError("Malformed token")

    message = f"{header_b64}.{body_b64}".encode()
    if not hmac.compare_digest(sig_b64, _sign(message, secret)):
        raise ValueError("Invalid signature")

    payload = json.loads(_b64_decode(body_b64))
    if payload.get("exp", 0) < time.time():
        raise ValueError("Token expired")
    return payload


def hash_jti(jti: str) -> str:
    return hashlib.sha256(jti.encode()).hexdigest()


def make_access_token(user_id: int, username: str, secret: str) -> str:
    now = int(time.time())
    return create_token(
        {
            "sub": str(user_id),
            "username": username,
            "type": "access",
            "iat": now,
            "exp": now + 15 * 60,
            "jti": secrets.token_hex(16),
        },
        secret,
    )


def make_refresh_token(user_id: int, username: str, secret: str) -> tuple[str, str]:
    """Returns (jwt_string, jti). Store hash_jti(jti) in the database."""
    now = int(time.time())
    jti = secrets.token_hex(32)
    token = create_token(
        {
            "sub": str(user_id),
            "username": username,
            "type": "refresh",
            "iat": now,
            "exp": now + 7 * 24 * 3600,
            "jti": jti,
        },
        secret,
    )
    return token, jti
