# Security Changes

## Authentication

**JWT-based login with httpOnly cookies**
- Added `POST /auth/login` — verifies username/password, issues access (15 min) + refresh (7 day) JWT pair stored as httpOnly, SameSite=strict cookies. No tokens in localStorage.
- Added `POST /auth/refresh` — rotates the refresh token on every use (old JTI revoked, new pair issued). Prevents replay attacks.
- Added `POST /auth/logout` — revokes the refresh token in the database and clears cookies.
- Added `GET /auth/me` — returns current user; frontend calls this on load to restore session.
- Added `POST /auth/change-password` — verifies old password, hashes new one, invalidates **all** sessions for the user.

**JWT implementation** uses Python stdlib only (`hmac`, `hashlib`, `base64`, `json`). HMAC-SHA256 signatures. No new PyPI dependencies.

**Password hashing** uses PBKDF2-SHA256 with 600,000 iterations (OWASP 2024 minimum) via Python's built-in `hashlib`. Salted with 32 random bytes.

**Refresh token storage**: only the SHA-256 hash of the JWT's `jti` claim is stored in the database. The raw token never touches the DB.

**Default admin user**: on first startup, if no users exist and `ADMIN_PASSWORD` is set in `.env`, one admin account is created automatically.

**New tables**: `users`, `refresh_tokens` — migration `a1b2c3d4e5f6_add_auth_tables`.

## Rate Limiting

- Login endpoint (`POST /auth/login`) is rate-limited to **5 attempts per IP per 15 minutes** using an in-memory `LoginRateLimiter`. Returns HTTP 429 on breach.
- Counter resets on successful login.

## All API Routes Protected

Added `dependencies=[Depends(get_current_user)]` to every router:
- `plants.py`, `readings.py`, `anomalies.py`, `commands.py`

All endpoints now return 401 without a valid access-token cookie.

## CORS Hardened

Changed `allow_origins=["*"]` to `allow_origins=[settings.FRONTEND_ORIGIN]` (default: `http://localhost:3000`). Only the dashboard origin may make cross-origin requests. Methods restricted to `GET, POST, DELETE`; headers to `Content-Type`.

## Security Headers

Added `SecurityHeadersMiddleware` (Starlette `BaseHTTPMiddleware`) on every response:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: default-src 'self'; ...`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`

## Error Sanitization

Added a global `exception_handler(Exception)` that catches unhandled exceptions and returns `{"detail": "Internal server error"}` in production (`DEBUG=false`). Stack traces never reach the HTTP response.

## MQTT Device-ID Verification

Added `_payload_device_id_matches()` in `mqtt_listener.py`. For every incoming status and ack message, if the JSON payload contains a `device_id` field, it is compared against the topic's device ID. Mismatches are **rejected and logged** at WARNING level:
```
SECURITY: rejected payload — topic device_id='leafnode-01' != payload device_id='leafnode-02'
```

## Secrets in .env

Added to `leafnode-backend/.env` (already gitignored):
- `JWT_SECRET` — 128-char hex string. **Must be changed before production deploy.**
- `DEBUG=true` — set to `false` in production to enable secure cookies and suppress stack traces.
- `FRONTEND_ORIGIN` — CORS allowed origin.
- `ADMIN_USERNAME`, `ADMIN_PASSWORD` — initial account credentials. **Change before deploy.**

No secrets exist in source code. All credentials are environment variables read via `pydantic-settings`.

## Input Sanitization

- All database queries use SQLAlchemy ORM parameterized queries throughout — no raw SQL.
- `device_id` path parameters already validated by regex `^[a-zA-Z0-9_\-]+$` in readings router.
- MQTT payload JSON is parsed with `json.loads` (no `eval`); schema is validated before use.
- Auth schemas (`LoginRequest`, `ChangePasswordRequest`) validate with Pydantic v2 validators.

## Frontend

- `api.js`: all requests include `credentials: 'include'` so cookies are sent automatically.
- On 401 response: attempts one silent token refresh (`POST /auth/refresh`), then retries the original request. If refresh also fails, throws `{ status: 401 }`.
- `App.jsx`: checks auth on mount via `GET /auth/me`. Shows `LoginPage` if unauthenticated. Sets `authState = false` on any 401 propagated from `fetchAll`.
- `LoginPage.jsx`: new component — username/password form, shows rate-limit and credential error messages. Uses Tailwind classes matching the existing design system.
- Logout button added to header (clears server-side session and shows login page).

## What Was NOT Changed

- No UI redesign — LoginPage uses the existing Tailwind `leaf` color palette and `btn-primary` class.
- No new npm packages added.
- All existing sensor reading, anomaly, plant profile, and command functionality preserved.
