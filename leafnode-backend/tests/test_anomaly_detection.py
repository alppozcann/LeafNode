"""
Tests for app/services/anomaly_detection.py

Covers the three public-facing units:
  _check_thresholds  – per-reading threshold violations
  _check_trends      – monotonic-trend detection over 3+ readings
  run_anomaly_detection – full detection + DB write + LLM explanation pipeline
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.anomaly_detection import (
    _check_thresholds,
    _check_trends,
    run_anomaly_detection,
)
from tests.conftest import make_reading, make_profile


# ---------------------------------------------------------------------------
# _check_thresholds
# ---------------------------------------------------------------------------

class TestCheckThresholds:
    def test_all_values_in_range_returns_empty(self):
        assert _check_thresholds(make_reading(), make_profile()) == []

    def test_temperature_above_max_is_detected(self):
        result = _check_thresholds(make_reading(temperature=35.0), make_profile())
        metrics = {a["metric"] for a in result}
        assert "temperature" in metrics
        assert all(a["rule_type"] == "threshold" for a in result)

    def test_humidity_below_min_is_detected(self):
        result = _check_thresholds(make_reading(humidity=10.0), make_profile())
        assert any(a["metric"] == "humidity" for a in result)

    def test_multiple_violations_all_reported(self):
        result = _check_thresholds(make_reading(temperature=35.0, humidity=10.0), make_profile())
        metrics = {a["metric"] for a in result}
        assert {"temperature", "humidity"}.issubset(metrics)

    def test_exact_boundary_value_is_not_a_violation(self):
        # Condition is strictly < or >, so boundary values must NOT trigger.
        result = _check_thresholds(make_reading(temperature=18.0), make_profile())
        assert not any(a["metric"] == "temperature" for a in result)

    def test_anomaly_dict_has_expected_shape(self):
        result = _check_thresholds(make_reading(temperature=40.0), make_profile())
        a = next(r for r in result if r["metric"] == "temperature")
        assert set(a.keys()) == {"metric", "value", "expected_min", "expected_max", "rule_type"}
        assert a["expected_min"] == 18.0
        assert a["expected_max"] == 28.0
        assert a["value"] == 40.0

    def test_soil_moisture_none_raises_type_error(self):
        # BUG (anomaly_detection.py:56): soil_moisture is nullable in the model;
        # comparing None < float raises TypeError and crashes anomaly detection.
        with pytest.raises(TypeError):
            _check_thresholds(make_reading(soil_moisture=None), make_profile())


# ---------------------------------------------------------------------------
# _check_trends
# ---------------------------------------------------------------------------

class TestCheckTrends:
    def test_single_reading_returns_empty(self):
        assert _check_trends([make_reading()]) == []

    def test_two_readings_returns_empty(self):
        assert _check_trends([make_reading(), make_reading()]) == []

    def test_monotonic_increase_above_delta_detected(self):
        # Temperature TREND_DELTA is 3.0; total change of +6 triggers detection.
        readings = [
            make_reading(temperature=20.0),
            make_reading(temperature=23.0),
            make_reading(temperature=26.0),
        ]
        result = _check_trends(readings)
        assert any(a["metric"] == "temperature" and a["rule_type"] == "trend" for a in result)

    def test_monotonic_decrease_above_delta_detected(self):
        readings = [
            make_reading(temperature=26.0),
            make_reading(temperature=23.0),
            make_reading(temperature=20.0),
        ]
        result = _check_trends(readings)
        assert any(a["metric"] == "temperature" for a in result)

    def test_trend_value_is_last_reading(self):
        readings = [
            make_reading(temperature=20.0),
            make_reading(temperature=23.0),
            make_reading(temperature=26.0),
        ]
        result = _check_trends(readings)
        temp = next(a for a in result if a["metric"] == "temperature")
        assert temp["value"] == 26.0

    def test_increase_below_delta_not_detected(self):
        # Total change 2.0 < delta 3.0 — should NOT trigger.
        readings = [
            make_reading(temperature=20.0),
            make_reading(temperature=21.0),
            make_reading(temperature=22.0),
        ]
        result = _check_trends(readings)
        assert not any(a["metric"] == "temperature" for a in result)

    def test_non_monotonic_sequence_not_detected(self):
        readings = [
            make_reading(temperature=20.0),
            make_reading(temperature=25.0),
            make_reading(temperature=21.0),  # dips back — breaks monotonicity
        ]
        result = _check_trends(readings)
        assert not any(a["metric"] == "temperature" for a in result)

    def test_flat_equal_values_not_detected(self):
        readings = [make_reading(temperature=22.0) for _ in range(3)]
        assert _check_trends(readings) == []

    def test_trend_anomaly_has_none_expected_bounds(self):
        readings = [
            make_reading(temperature=20.0),
            make_reading(temperature=23.0),
            make_reading(temperature=26.0),
        ]
        result = _check_trends(readings)
        temp = next(a for a in result if a["metric"] == "temperature")
        assert temp["expected_min"] is None
        assert temp["expected_max"] is None


# ---------------------------------------------------------------------------
# run_anomaly_detection
# ---------------------------------------------------------------------------

class TestRunAnomalyDetection:
    def _make_db(self, profile, recent_readings):
        """Return an AsyncMock DB session wired up with the given profile and readings."""
        profile_result = MagicMock()
        profile_result.scalar_one_or_none.return_value = profile

        readings_result = MagicMock()
        readings_result.scalars.return_value.all.return_value = recent_readings

        db = AsyncMock()
        db.execute.side_effect = [profile_result, readings_result]
        db.add_all = MagicMock()  # sync in SQLAlchemy — must not be AsyncMock
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    async def test_no_profile_returns_empty_list(self):
        db = AsyncMock()
        no_profile = MagicMock()
        no_profile.scalar_one_or_none.return_value = None
        db.execute.return_value = no_profile

        result = await run_anomaly_detection(db, make_reading())

        assert result == []
        db.add_all.assert_not_called()

    async def test_clean_reading_no_anomalies_returns_empty(self):
        # All sensor values are within profile thresholds — nothing fires.
        reading = make_reading()
        db = self._make_db(profile=make_profile(), recent_readings=[reading])

        with patch("app.services.anomaly_detection.generate_explanation", new_callable=AsyncMock) as mock_llm:
            result = await run_anomaly_detection(db, reading)

        assert result == []
        mock_llm.assert_not_awaited()

    async def test_threshold_anomaly_calls_llm_and_attaches_explanation(self):
        reading = make_reading(temperature=40.0)  # exceeds profile max of 28.0
        db = self._make_db(profile=make_profile(), recent_readings=[reading])
        explanation_text = "Temperature is dangerously high for Basil."

        with patch(
            "app.services.anomaly_detection.generate_explanation",
            new_callable=AsyncMock,
            return_value=explanation_text,
        ):
            records = await run_anomaly_detection(db, reading)

        assert len(records) > 0
        assert all(r.explanation == explanation_text for r in records)
        db.flush.assert_awaited_once()
        db.commit.assert_awaited_once()

    async def test_llm_failure_stores_anomaly_without_explanation(self):
        # LLM returning None must not block the anomaly from being persisted.
        reading = make_reading(temperature=40.0)
        db = self._make_db(profile=make_profile(), recent_readings=[reading])

        with patch(
            "app.services.anomaly_detection.generate_explanation",
            new_callable=AsyncMock,
            return_value=None,
        ):
            records = await run_anomaly_detection(db, reading)

        assert len(records) > 0
        assert all(r.explanation is None for r in records)
        db.commit.assert_awaited_once()

    async def test_trend_anomaly_detected_with_three_readings(self):
        r1 = make_reading(temperature=20.0)
        r2 = make_reading(temperature=23.0)
        r3 = make_reading(temperature=26.0)  # latest; total delta=6 > threshold 3.0
        db = self._make_db(profile=make_profile(), recent_readings=[r1, r2, r3])

        with patch(
            "app.services.anomaly_detection.generate_explanation",
            new_callable=AsyncMock,
            return_value="Trend detected.",
        ):
            records = await run_anomaly_detection(db, r3)

        rule_types = {r.rule_type for r in records}
        assert "trend" in rule_types
