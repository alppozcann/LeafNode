import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.influx_listener import influx_listener
from app.influx_client import InfluxDBManager
from app.routers import anomalies, plants, readings, commands
from app.services.mqtt_listener import mqtt_ack_listener

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task_influx = asyncio.create_task(influx_listener())
    task_mqtt = asyncio.create_task(mqtt_ack_listener())
    logger.info("InfluxDB and MQTT listeners started")
    try:
        yield
    finally:
        task_influx.cancel()
        task_mqtt.cancel()
        try:
            await asyncio.gather(task_influx, task_mqtt)
        except asyncio.CancelledError:
            pass
        logger.info("Background listeners stopped")
        await InfluxDBManager.close()
        logger.info("InfluxDB connection closed")


app = FastAPI(
    title="LeafNode",
    description="Plant monitoring backend — MQTT ingestion, anomaly detection, LLM explanations",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plants.router)
app.include_router(readings.router)
app.include_router(anomalies.router)
app.include_router(commands.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
