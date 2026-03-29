# LeafNode Backend

Plant monitoring backend — real-time MQTT ingestion, deterministic anomaly detection, and LLM-powered explanations via Claude.

## Stack

| Layer | Library |
|---|---|
| API | FastAPI |
| Database | PostgreSQL + SQLAlchemy (async) |
| Migrations | Alembic |
| MQTT | asyncio-mqtt |
| LLM | Anthropic Python SDK |
| Validation | Pydantic v2 |
| Config | pydantic-settings + python-dotenv |

---

## Setup

### 1. Clone & install dependencies

```bash
cd leafnode-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your values
```

Key variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | asyncpg connection string |
| `MQTT_BROKER_HOST` | MQTT broker hostname |
| `MQTT_BROKER_PORT` | MQTT broker port (default 1883) |
| `MQTT_TOPIC` | Topic to subscribe to |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `CLAUDE_MODEL` | Claude model ID |
| `TREND_DELTA_*` | Per-metric trend detection thresholds |

### 3. Create PostgreSQL database

```bash
psql -U postgres -c "CREATE DATABASE leafnode;"
```

### 4. Run migrations

```bash
alembic upgrade head
```

### 5. Start the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The MQTT listener starts automatically as a background task via FastAPI's `lifespan` hook.

---

## MQTT Payload Format

Publish to the configured topic (default: `leafnode/sensors`):

```json
{
    "device_id": "leafnode-01",
    "wake_count": 3,
    "temperature": 23.45,
    "humidity": 58.10,
    "pressure": 1012.30,
    "light": 1873
}
```

On every message the backend will:
1. Validate and store the reading
2. Run threshold + trend anomaly detection against the device's plant profile
3. If anomalies are found, call Claude for a plain-English explanation and store it

---

## API Reference

### Health

```bash
curl http://localhost:8000/health
```

---

### Plants

**Register a plant profile for a device** (calls Claude to generate thresholds):

```bash
curl -X POST http://localhost:8000/plants \
  -H "Content-Type: application/json" \
  -d '{"plant_name": "Monstera deliciosa", "device_id": "leafnode-01"}'
```

**Get plant profile for a device:**

```bash
curl http://localhost:8000/plants/leafnode-01
```

---

### Readings

**Get last 50 readings for a device:**

```bash
curl http://localhost:8000/readings/leafnode-01
```

**Get last N readings (custom limit):**

```bash
curl "http://localhost:8000/readings/leafnode-01?limit=10"
```

**Get latest single reading:**

```bash
curl http://localhost:8000/readings/leafnode-01/latest
```

---

### Anomalies

**Get anomaly records with LLM explanations:**

```bash
curl http://localhost:8000/anomalies/leafnode-01
```

**Get latest anomaly:**

```bash
curl http://localhost:8000/anomalies/leafnode-01/latest
```

---

## Anomaly Detection Logic

### Threshold violations
Every metric (`temperature`, `humidity`, `pressure`, `light`) is compared against the stored plant profile thresholds. A reading outside `[min, max]` triggers a `threshold` anomaly.

### Trend detection
After each reading, the last 3 readings for the device are loaded. If a metric is **monotonically increasing or decreasing** and the total change exceeds the configured delta, a `trend` anomaly is triggered.

| Env var | Default | Description |
|---|---|---|
| `TREND_DELTA_TEMPERATURE` | `3.0` | °C change across 3 readings |
| `TREND_DELTA_HUMIDITY` | `10.0` | % change across 3 readings |
| `TREND_DELTA_PRESSURE` | `5.0` | hPa change across 3 readings |
| `TREND_DELTA_LIGHT` | `500.0` | lux change across 3 readings |

### LLM explanation
When anomalies are found, a single Claude call is made with:
- Plant name
- Current readings
- All detected anomaly details
- Last 3 readings for trend context

Claude explains the conditions and suggests corrective actions. It does **not** decide what is or isn't an anomaly. If the LLM call fails, anomalies are stored without an explanation and the error is logged.

---

## Project Structure

```
leafnode-backend/
├── app/
│   ├── main.py               # FastAPI app, lifespan, CORS, router registration
│   ├── config.py             # Settings via pydantic-settings
│   ├── database.py           # Async engine, session factory, Base
│   ├── mqtt_client.py        # asyncio-mqtt listener with auto-reconnect
│   ├── models/
│   │   ├── sensor_reading.py
│   │   ├── plant_profile.py
│   │   └── anomaly_record.py
│   ├── schemas/
│   │   ├── sensor_reading.py
│   │   ├── plant_profile.py
│   │   └── anomaly_record.py
│   ├── services/
│   │   ├── anomaly_detection.py  # Threshold + trend engine
│   │   ├── llm_threshold.py      # Claude call for threshold generation
│   │   └── llm_explanation.py    # Claude call for anomaly explanation
│   ├── routers/
│   │   ├── plants.py
│   │   ├── readings.py
│   │   └── anomalies.py
│   └── core/
│       └── prompts.py        # All LLM prompt templates
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial_schema.py
├── alembic.ini
├── .env.example
├── requirements.txt
└── README.md
```
