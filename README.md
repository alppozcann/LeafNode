# LeafNode

A full-stack IoT plant monitoring system. ESP32 devices publish sensor readings to InfluxDB; the backend polls for new data every 10 seconds, runs anomaly detection, and calls Google Gemini to generate plain-English explanations.

---

## Architecture

```
ESP32 Device
    │  (sensor data via MQTT)
    ▼
InfluxDB
    │
    │  poll every 10s
    ▼
FastAPI Backend
    ├── PostgreSQL  (SensorReadings, PlantProfiles, AnomalyRecords)
    ├── Google Gemini  (threshold generation + anomaly explanations)
    └── MQTT  (device command dispatch + ACK listener)
         │
         ▼
    ESP32 Device  (receives watering / LED commands)
```

**Data flow in detail:**
1. The backend's InfluxDB listener polls for readings newer than the last check time.
2. Each new reading is written to PostgreSQL as a `SensorReading`.
3. Anomaly detection runs — threshold check (value vs. plant profile min/max) and trend check (monotonic delta over the last 3 readings).
4. If anomalies are found, a single Gemini call generates one explanation attached to all `AnomalyRecord` rows for that reading.

---

## Prerequisites

| Service | Purpose |
|---|---|
| PostgreSQL ≥ 14 | Persistent storage for plants, readings, anomalies |
| InfluxDB 2.x | Time-series store that receives device sensor data |
| MQTT broker | Receives device telemetry; relays commands back to devices |
| Python 3.10+ | Backend runtime |
| Google Gemini API key | LLM features (threshold generation + explanations) |

---

## Setup

```bash
cd leafnode-backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Open .env and fill in the values below

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

Edit `leafnode-backend/.env`:

```env
# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/leafnode

# InfluxDB
INFLUXDB_URL=http://localhost:8086
INFLUXDB_USERNAME=
INFLUXDB_PASSWORD=
INFLUXDB_ORG=leafnode-org
INFLUXDB_BUCKET=leafnode-bucket
INFLUXDB_MEASUREMENT=sensor_reading

# Google Gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash-lite

# MQTT
MQTT_BROKER=your.broker.host
MQTT_PORT=1883
MQTT_USER=
MQTT_PASS=

# Trend detection sensitivity (total change across 3 readings that triggers an alert)
TREND_DELTA_TEMPERATURE=3.0
TREND_DELTA_HUMIDITY=10.0
TREND_DELTA_LIGHT=500.0
TREND_DELTA_PRESSURE=5.0
TREND_DELTA_SOIL_MOISTURE=15.0
```

---

## API Reference

All endpoints are served at `http://localhost:8000`.

### Health

```
GET /health
```

### Plants

```
POST /plants                       Register a plant profile (calls Gemini for thresholds)
GET  /plants/{device_id}           Get the plant profile for a device
```

**Register example:**
```bash
curl -X POST http://localhost:8000/plants \
  -H "Content-Type: application/json" \
  -d '{"plant_name": "Monstera", "device_id": "leafnode-01"}'
```

### Readings

```
GET /readings/{device_id}                  Historical readings (default 3h window)
GET /readings/{device_id}?range=1d         Supported: 30m 1h 3h 6h 12h 1d 5d 10d 15d 30d
GET /readings/{device_id}/latest           Single latest reading
```

### Anomalies

```
GET    /anomalies/{device_id}              List anomalies (default limit 50)
GET    /anomalies/{device_id}?limit=10     Custom limit (1–1000)
GET    /anomalies/{device_id}/latest       Latest anomaly
DELETE /anomalies/{anomaly_id}             Resolve (delete) a specific anomaly → 204
```

### Device Commands

```
POST /devices/{device_id}/command          Send a command to the device via MQTT
```

**Command example:**
```bash
curl -X POST http://localhost:8000/devices/leafnode-01/command \
  -H "Content-Type: application/json" \
  -d '{"cmd": "water", "times": 3}'
```

Commands are queued and delivered during the device's next 35-second wake window.

---

## Anomaly Detection

### Threshold violations

Every metric is compared against the plant profile's `[min, max]` range. A reading outside the range creates a `threshold` anomaly record.

### Trend detection

After each reading, the last 3 stored readings are loaded. If a metric is **monotonically increasing or decreasing** and the total change exceeds the configured `TREND_DELTA_*`, a `trend` anomaly is created. Requires at least 3 readings in the database.

### LLM explanation

When anomalies are found, a single Gemini call receives the plant name, current sensor values, all detected anomalies, and the last 3 readings for trend context. It returns a 3–5 sentence plain-English explanation attached to every anomaly record for that reading. If the call fails, anomalies are stored without an explanation and the error is logged.

---

## Running Tests

No external services are needed — all DB, LLM, MQTT, and HTTP calls are mocked.

```bash
cd leafnode-backend
source .venv/bin/activate

# Install test dependencies (one-time)
pip install -r requirements-test.txt

# Run all tests
.venv/bin/python -m pytest

# Run a specific file
.venv/bin/python -m pytest tests/test_anomaly_detection.py

# Run a single test by name
.venv/bin/python -m pytest tests/test_anomaly_detection.py::TestCheckTrends::test_monotonic_increase_above_delta_detected

# Verbose output
.venv/bin/python -m pytest -v

# Coverage report (requires pytest-cov)
pip install pytest-cov
.venv/bin/python -m pytest --cov=app --cov-report=term-missing
```

> **Note:** Always use `.venv/bin/python -m pytest` rather than bare `pytest`. If Anaconda is installed, the shell `pytest` command may resolve to the system Python and fail.

| File | Tests | What it covers |
|---|---|---|
| `tests/test_anomaly_detection.py` | 21 | `_check_thresholds`, `_check_trends`, `run_anomaly_detection` — includes the `soil_moisture=None` crash regression |
| `tests/test_anomaly_router.py` | 8 | `DELETE /anomalies/{id}` (204/404/422) and `GET /anomalies/{device_id}` |
| `tests/test_llm_threshold.py` | 8 | `generate_thresholds` — valid JSON, markdown-fenced responses, missing keys, invalid JSON, Gemini API errors |

---

## Deploying to the Cloud

### 1. Managed data services

Provision these before deploying any code:

| Service | Recommended option |
|---|---|
| PostgreSQL | Supabase, Railway, Render Postgres, AWS RDS |
| InfluxDB | InfluxDB Cloud (free tier available at influxdata.com) |
| MQTT broker | HiveMQ Cloud, EMQX Cloud, or your existing broker |

### 2. Backend

**Recommended: Railway or Render (simplest)**

1. Connect your GitHub repo.
2. Set the root directory to `leafnode-backend`.
3. Set the start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add all environment variables via the platform's secret/env UI.
5. Run migrations once after first deploy: `alembic upgrade head`

**Alternative: Docker**

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

> **Important:** Remove all hardcoded credential defaults from `config.py` before pushing to a public repository.

### 3. Pre-launch checklist

- [ ] All secrets are in environment variables — no hardcoded passwords in `config.py`
- [ ] `alembic upgrade head` has been run against the production database
- [ ] `GEMINI_API_KEY` is set and the model name is valid
- [ ] InfluxDB bucket, org, and measurement names match what the ESP32 devices write to
- [ ] MQTT broker is reachable from the backend host (check firewall/port 1883)
- [ ] Backend is behind HTTPS (most platforms provide this automatically)

---

## Database Migrations

```bash
cd leafnode-backend
source .venv/bin/activate

# Apply all pending migrations
alembic upgrade head

# Generate a new migration after changing a model
alembic revision --autogenerate -m "describe the change"

# Roll back one migration
alembic downgrade -1
```

---

## Project Structure

```
LeafNode/
└── leafnode-backend/
    ├── app/
    │   ├── main.py                 FastAPI app, lifespan, CORS, router registration
    │   ├── config.py               All settings via pydantic-settings (.env)
    │   ├── database.py             Async SQLAlchemy engine + session factory
    │   ├── influx_client.py        InfluxDB async client (static class)
    │   ├── influx_listener.py      10s polling loop → ingestion → anomaly detection
    │   ├── models/                 SQLAlchemy ORM models
    │   ├── schemas/                Pydantic v2 request/response schemas
    │   ├── routers/                REST endpoints (plants, readings, anomalies, commands)
    │   ├── services/
    │   │   ├── anomaly_detection.py    Threshold + trend engine
    │   │   ├── llm_explanation.py      Gemini call for anomaly explanation
    │   │   ├── llm_threshold.py        Gemini call for threshold generation
    │   │   └── mqtt_listener.py        MQTT ACK listener for device commands
    │   └── core/prompts.py         Gemini prompt templates
    ├── alembic/                    Database migration scripts
    ├── tests/                      Pytest test suite (no external services needed)
    ├── requirements.txt
    ├── requirements-test.txt
    └── .env.example
```
