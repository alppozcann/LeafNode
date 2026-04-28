import hashlib
import hmac
import secrets

_ITERATIONS = 600_000
_ALG = "sha256"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(32)
    dk = hashlib.pbkdf2_hmac(_ALG, password.encode(), salt.encode(), _ITERATIONS)
    return f"pbkdf2:{_ALG}:{_ITERATIONS}:{salt}:{dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, alg, iterations_str, salt, dk_hex = stored.split(":")
        dk = hashlib.pbkdf2_hmac(alg, password.encode(), salt.encode(), int(iterations_str))
        return hmac.compare_digest(dk.hex(), dk_hex)
    except (ValueError, AttributeError):
        return False
