"""
Tests for app/routers/anomalies.py

Uses a minimal FastAPI app containing only the anomaly router so the test
process never starts the InfluxDB / MQTT background listeners.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.routers.anomalies import router
from app.database import get_db

# Minimal app — no lifespan, no background tasks.
anomaly_app = FastAPI()
anomaly_app.include_router(router)


def make_anomaly_record(**overrides):
    defaults = {
        "id": 1,
        "device_id": "device-01",
        "sensor_reading_id": 10,
        "metric": "temperature",
        "value": 35.0,
        "expected_min": 18.0,
        "expected_max": 28.0,
        "rule_type": "threshold",
        "explanation": "Too hot.",
        "timestamp": datetime(2024, 6, 1, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    m = MagicMock()
    for k, v in defaults.items():
        setattr(m, k, v)
    return m


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture(autouse=True)
def override_db(mock_db):
    async def _get_db():
        yield mock_db

    anomaly_app.dependency_overrides[get_db] = _get_db
    yield
    anomaly_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# DELETE /anomalies/{anomaly_id}
# ---------------------------------------------------------------------------

class TestDeleteAnomaly:
    async def test_existing_record_returns_204(self, mock_db):
        record = make_anomaly_record()
        exec_result = MagicMock()
        exec_result.scalar_one_or_none.return_value = record
        mock_db.execute.return_value = exec_result

        async with AsyncClient(transport=ASGITransport(app=anomaly_app), base_url="http://test") as ac:
            response = await ac.delete("/anomalies/1")

        assert response.status_code == 204
        mock_db.delete.assert_awaited_once_with(record)
        mock_db.commit.assert_awaited_once()

    async def test_nonexistent_record_returns_404(self, mock_db):
        exec_result = MagicMock()
        exec_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = exec_result

        async with AsyncClient(transport=ASGITransport(app=anomaly_app), base_url="http://test") as ac:
            response = await ac.delete("/anomalies/999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Anomaly not found"
        mock_db.delete.assert_not_awaited()
        mock_db.commit.assert_not_awaited()

    async def test_string_id_returns_422(self, mock_db):
        # FastAPI path-param coercion: "abc" → int fails → 422 Unprocessable Entity
        async with AsyncClient(transport=ASGITransport(app=anomaly_app), base_url="http://test") as ac:
            response = await ac.delete("/anomalies/not-a-number")

        assert response.status_code == 422

    async def test_delete_response_body_is_empty(self, mock_db):
        record = make_anomaly_record()
        exec_result = MagicMock()
        exec_result.scalar_one_or_none.return_value = record
        mock_db.execute.return_value = exec_result

        async with AsyncClient(transport=ASGITransport(app=anomaly_app), base_url="http://test") as ac:
            response = await ac.delete("/anomalies/1")

        assert response.content == b""


# ---------------------------------------------------------------------------
# GET /anomalies/{device_id}
# ---------------------------------------------------------------------------

class TestGetAnomalies:
    async def test_returns_list_for_device(self, mock_db):
        records = [make_anomaly_record(id=i) for i in range(3)]
        exec_result = MagicMock()
        exec_result.scalars.return_value.all.return_value = records
        mock_db.execute.return_value = exec_result

        async with AsyncClient(transport=ASGITransport(app=anomaly_app), base_url="http://test") as ac:
            response = await ac.get("/anomalies/device-01")

        assert response.status_code == 200
        assert len(response.json()) == 3

    async def test_returns_empty_list_when_no_anomalies(self, mock_db):
        exec_result = MagicMock()
        exec_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = exec_result

        async with AsyncClient(transport=ASGITransport(app=anomaly_app), base_url="http://test") as ac:
            response = await ac.get("/anomalies/quiet-device")

        assert response.status_code == 200
        assert response.json() == []

    async def test_limit_query_param_is_accepted(self, mock_db):
        exec_result = MagicMock()
        exec_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = exec_result

        async with AsyncClient(transport=ASGITransport(app=anomaly_app), base_url="http://test") as ac:
            response = await ac.get("/anomalies/device-01?limit=5")

        assert response.status_code == 200

    async def test_limit_zero_returns_422(self, mock_db):
        async with AsyncClient(transport=ASGITransport(app=anomaly_app), base_url="http://test") as ac:
            response = await ac.get("/anomalies/device-01?limit=0")

        assert response.status_code == 422
