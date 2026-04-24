from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest


def make_reading(**overrides):
    """MagicMock SensorReading with all fields at safe in-range defaults."""
    defaults = {
        "id": 1,
        "device_id": "device-01",
        "wake_count": 1,
        "temperature": 22.0,
        "humidity": 60.0,
        "pressure": 1013.0,
        "light": 500.0,
        "soil_moisture": 50.0,
        "timestamp": datetime(2024, 6, 1, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    m = MagicMock()
    for k, v in defaults.items():
        setattr(m, k, v)
    return m


def make_profile(**overrides):
    """MagicMock PlantProfile whose thresholds match make_reading() defaults."""
    defaults = {
        "device_id": "device-01",
        "plant_name": "Basil",
        "temperature_min": 18.0,
        "temperature_max": 28.0,
        "humidity_min": 40.0,
        "humidity_max": 80.0,
        "pressure_min": 1000.0,
        "pressure_max": 1030.0,
        "light_min": 200.0,
        "light_max": 2000.0,
        "soil_moisture_min": 30.0,
        "soil_moisture_max": 70.0,
    }
    defaults.update(overrides)
    m = MagicMock()
    for k, v in defaults.items():
        setattr(m, k, v)
    return m
