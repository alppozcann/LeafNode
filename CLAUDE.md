# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is LeafNode

IoT plant monitoring system. ESP32 devices publish sensor readings (temperature, humidity, pressure, light, soil moisture) to InfluxDB. The backend polls InfluxDB every 10s, stores readings to PostgreSQL, runs anomaly detection, and calls Google Gemini to generate plain-English explanations. The React frontend connects per-device and displays live charts and anomaly feeds.

## Commands

### Backend
```bash
cd leafnode-backend
source .venv/bin/activate
alembic upgrade head                              # run migrations
uvicorn app.main:app --reload --port 8000         # start server
```

### Frontend
```bash
cd leafnode-frontend
npm run dev       # Vite dev server at http://localhost:3000
npm run build
```

### Combined startup
```bash
./start.sh        # handles venv activation, migrations, and starts both services
```

## Architecture

### Data flow
1. InfluxDB listener (`app/influx_listener.py`) polls InfluxDB every 10s
2. Each new reading is written to PostgreSQL as a `SensorReading`
3. Anomaly detection runs — threshold check against `PlantProfile` min/max + trend check (monotonic delta over last 3 readings)
4. If anomalies found, a single Gemini call generates an explanation attached to all `AnomalyRecord`s for that reading
5. Frontend auto-refreshes every 30s via REST API calls proxied from Vite → FastAPI

### Backend (`leafnode-backend/app/`)
- `main.py` — FastAPI app, lifespan hooks that start InfluxDB listener and MQTT listener, CORS config
- `config.py` — All settings via pydantic-settings (env vars for DB, InfluxDB, Gemini, MQTT, trend deltas)
- `influx_listener.py` — Core polling loop; orchestrates ingestion + anomaly detection
- `influx_client.py` — Async InfluxDB client (static class)
- `services/anomaly_detection.py` — Threshold and trend detection logic
- `services/llm_explanation.py` — Gemini call for anomaly explanation
- `services/llm_threshold.py` — Gemini call to generate thresholds when registering a new plant type
- `services/mqtt_listener.py` — MQTT ACK listener for device commands
- `core/prompts.py` — All Gemini prompt templates
- `routers/` — REST endpoints: `/plants`, `/readings`, `/anomalies`, `/devices/{id}/command`
- `models/` — SQLAlchemy async ORM: `SensorReading`, `PlantProfile`, `AnomalyRecord`
- `schemas/` — Pydantic v2 request/response schemas

### Frontend (`leafnode-frontend/src/`)
- `App.jsx` — Root: device connection input, per-device state, 30s polling
- `api.js` — All fetch calls (plants, readings, anomalies, commands)
- `components/` — `PlantPanel`, `MetricsGrid`, `ReadingsChart` (Recharts), `AnomalyFeed`, `PlantSelectorModal`
- `vite.config.js` — Proxies `/api` → `http://localhost:8000`
- Tailwind uses a custom `leaf` green color palette (`tailwind.config.js`)

### Key technologies
- **Backend:** FastAPI, SQLAlchemy 2 (async/asyncpg), Alembic, InfluxDB client, aiomqtt, Google Gemini (`google-genai`)
- **Frontend:** React 18, Vite, Tailwind CSS, Recharts

## Environment Variables

Backend reads from `leafnode-backend/.env`. Key variables:
```
DATABASE_URL=postgresql+asyncpg://...
INFLUXDB_URL, INFLUXDB_ORG, INFLUXDB_BUCKET, INFLUXDB_MEASUREMENT
GEMINI_API_KEY, GEMINI_MODEL
MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASS
TREND_DELTA_TEMPERATURE/HUMIDITY/LIGHT/PRESSURE/SOIL_MOISTURE  # anomaly sensitivity
```

## Database Migrations

Migrations live in `leafnode-backend/alembic/versions/`. Always run `alembic upgrade head` after pulling schema changes. Generate a new migration with:
```bash
alembic revision --autogenerate -m "description"
```
