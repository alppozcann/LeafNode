import logging
from datetime import datetime
from typing import Optional

from influxdb_client import Point
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

from app.config import settings
from app.models.sensor_reading import SensorReading

logger = logging.getLogger(__name__)

class InfluxDBManager:
    client: Optional[InfluxDBClientAsync] = None

    @classmethod
    def get_client(cls) -> InfluxDBClientAsync:
        if cls.client is None:
            cls.client = InfluxDBClientAsync(
                url=settings.INFLUXDB_URL,
                username=settings.INFLUXDB_USERNAME,
                password=settings.INFLUXDB_PASSWORD,
                org=settings.INFLUXDB_ORG,
            )
        return cls.client

    @classmethod
    async def close(cls):
        if cls.client is not None:
            await cls.client.close()
            cls.client = None

    @classmethod
    async def write_sensor_reading(cls, reading: SensorReading):
        """Write a sensor reading to InfluxDB."""
        client = cls.get_client()
        write_api = client.write_api()

        point = (
            Point(settings.INFLUXDB_MEASUREMENT)
            .tag("device_id", reading.device_id)
            .field("temperature", float(reading.temperature))
            .field("humidity", float(reading.humidity))
            .field("pressure", float(reading.pressure))
            .field("light", float(reading.light))
            .field("wake_count", int(reading.wake_count))
            .time(reading.timestamp)
        )

        try:
            await write_api.write(bucket=settings.INFLUXDB_BUCKET, org=settings.INFLUXDB_ORG, record=point)
            logger.debug(f"Successfully wrote sensor data for {reading.device_id} to InfluxDB")
        except Exception as e:
            logger.exception(f"Failed to write sensor data to InfluxDB: {e}")

    @classmethod
    async def query_sensor_readings(cls, device_id: str, time_range: str = "3h", limit: int = None) -> list[dict]:
        client = cls.get_client()
        query_api = client.query_api()
        
        safe_dev = device_id.replace('"', '\\"')

        if limit is not None:
            query = f'''
            from(bucket: "{settings.INFLUXDB_BUCKET}")
              |> range(start: -30d)
              |> filter(fn: (r) => r["_measurement"] == "{settings.INFLUXDB_MEASUREMENT}")
              |> filter(fn: (r) => r["topic"] == "group1/{safe_dev}")
              |> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "humidity" or r["_field"] == "pressure" or r["_field"] == "light" or r["_field"] == "light_lux" or r["_field"] == "soil_raw" or r["_field"] == "soil_moisture" or r["_field"] == "wake_count" or r["_field"] == "bme_ok" or r["_field"] == "soil_ok" or r["_field"] == "ldr_ok")
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
              |> sort(columns: ["_time"], desc: true)
              |> limit(n: {limit})
            '''
        else:
            window_mapping = {
                "30m": "30s", "1h": "1m",
                "3h": "2m", "6h": "5m", "12h": "10m",
                "1d": "20m", "5d": "1h", "10d": "2h",
                "15d": "3h", "30d": "6h"
            }
            window = window_mapping.get(time_range, "10m")
            query = f'''
            from(bucket: "{settings.INFLUXDB_BUCKET}")
              |> range(start: -{time_range})
              |> filter(fn: (r) => r["_measurement"] == "{settings.INFLUXDB_MEASUREMENT}")
              |> filter(fn: (r) => r["topic"] == "group1/{safe_dev}")
              |> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "humidity" or r["_field"] == "pressure" or r["_field"] == "light" or r["_field"] == "light_lux" or r["_field"] == "soil_raw" or r["_field"] == "soil_moisture" or r["_field"] == "wake_count")
              |> aggregateWindow(every: {window}, fn: mean, createEmpty: false)
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
              |> sort(columns: ["_time"], desc: true)
            '''
        
        try:
            result = await query_api.query(query, org=settings.INFLUXDB_ORG)
            readings = []
            for table in result:
                for record in table.records:
                    # Generate stable mock ID using hash to satisfy schema requirements
                    dev_id = str(record.values.get("topic", "")).split("/")[-1] if record.values.get("topic") else str(record.values.get("device_id", device_id))
                    stable_id = abs(hash(dev_id + str(record.get_time().timestamp()))) % (10**9)
                    
                    def s_flt(v, d=0.0):
                        try:
                            return float(v) if v is not None else d
                        except (TypeError, ValueError):
                            return d

                    def s_int(v, d=0):
                        try:
                            return int(float(v)) if v is not None else d
                        except (TypeError, ValueError):
                            return d

                    # Influx fields might come back as floats or ints
                    readings.append({
                        "id": stable_id,
                        "device_id": dev_id,
                        "temperature": s_flt(record.values.get("temperature", 0.0)),
                        "humidity": s_flt(record.values.get("humidity", 0.0)),
                        "pressure": s_flt(record.values.get("pressure", 0.0)),
                        "light": s_flt(record.values.get("light_lux", record.values.get("light", 0.0))),
                        "temperature_raw": s_flt(record.values.get("temperature_raw", 0.0)) if "temperature_raw" in record.values else None,
                        "humidity_raw": s_flt(record.values.get("humidity_raw", 0.0)) if "humidity_raw" in record.values else None,
                        "pressure_raw": s_flt(record.values.get("pressure_raw", 0.0)) if "pressure_raw" in record.values else None,
                        "soil_raw": s_int(record.values.get("soil_raw", 0)) if "soil_raw" in record.values else None,
                        "soil_moisture": s_int(record.values.get("soil_moisture", 0)) if "soil_moisture" in record.values else None,
                        "bme_ok": bool(record.values.get("bme_ok")) if "bme_ok" in record.values else None,
                        "soil_ok": bool(record.values.get("soil_ok")) if "soil_ok" in record.values else None,
                        "ldr_ok": bool(record.values.get("ldr_ok")) if "ldr_ok" in record.values else None,
                        "wake_count": s_int(record.values.get("wake_count", 0)),
                        "timestamp": record.get_time(),
                    })
            return readings
        except Exception as e:
            logger.exception(f"Failed to query InfluxDB: {e}")
            return []

    @classmethod
    async def query_recent_readings(cls, start_time: datetime) -> list[dict]:
        client = cls.get_client()
        query_api = client.query_api()
        
        start_iso = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        query = f'''
        from(bucket: "{settings.INFLUXDB_BUCKET}")
          |> range(start: {start_iso})
          |> filter(fn: (r) => r["_measurement"] == "{settings.INFLUXDB_MEASUREMENT}")
          |> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "humidity" or r["_field"] == "pressure" or r["_field"] == "light" or r["_field"] == "light_lux" or r["_field"] == "soil_raw" or r["_field"] == "soil_moisture" or r["_field"] == "wake_count")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> sort(columns: ["_time"], desc: false)
        '''
        
        try:
            result = await query_api.query(query, org=settings.INFLUXDB_ORG)
            readings = []
            for table in result:
                for record in table.records:
                    if record.get_time() <= start_time:
                        continue # Filter inclusive boundary out
                    def s_flt(v, d=0.0):
                        try:
                            return float(v) if v is not None else d
                        except (TypeError, ValueError):
                            return d

                    def s_int(v, d=0):
                        try:
                            return int(float(v)) if v is not None else d
                        except (TypeError, ValueError):
                            return d

                    readings.append({
                        "device_id": str(record.values.get("topic", "")).split("/")[-1] if record.values.get("topic") else str(record.values.get("device_id", "unknown")),
                        "temperature": s_flt(record.values.get("temperature", 0.0)),
                        "humidity": s_flt(record.values.get("humidity", 0.0)),
                        "pressure": s_flt(record.values.get("pressure", 0.0)),
                        "light": s_flt(record.values.get("light_lux", record.values.get("light", 0.0))),
                        "soil_moisture": s_flt(record.values.get("soil_moisture", 0.0)),
                        "wake_count": s_int(record.values.get("wake_count", 0)),
                        "timestamp": record.get_time(),
                    })
            return readings
        except Exception as e:
            logger.exception(f"Failed to query recent readings from InfluxDB: {e}")
            return []


