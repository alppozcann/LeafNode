import logging

from google import genai
from google.genai.errors import APIError

from app.config import settings
from app.core.prompts import ANOMALY_EXPLANATION_PROMPT
from app.models.anomaly_record import AnomalyRecord
from app.models.sensor_reading import SensorReading

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.GEMINI_API_KEY)


def _format_anomaly_list(anomalies: list[AnomalyRecord]) -> str:
    lines = []
    for a in anomalies:
        if a.rule_type == "threshold":
            lines.append(
                f"- {a.metric}: value={a.value}, expected [{a.expected_min}, {a.expected_max}] (threshold violation)"
            )
        else:
            lines.append(
                f"- {a.metric}: value={a.value}, monotonic trend detected (trend violation)"
            )
    return "\n".join(lines)


def _format_trend_context(readings: list[SensorReading]) -> str:
    if not readings:
        return "No prior readings available."
    lines = []
    for r in readings:
        lines.append(
            f"  [{r.timestamp.isoformat()}] temp={r.temperature}°C, "
            f"humidity={r.humidity}%, pressure={r.pressure} hPa, light={r.light} lux"
        )
    return "\n".join(lines)


async def generate_explanation(
    plant_name: str,
    current_reading: SensorReading,
    anomalies: list[AnomalyRecord],
    recent_readings: list[SensorReading],
) -> str | None:
    """Call Gemini to produce a plain-English explanation for the detected anomalies.

    Returns the explanation string, or None if the call fails (caller should
    store the anomaly without explanation and log the error).
    """
    prompt = ANOMALY_EXPLANATION_PROMPT.format(
        plant_name=plant_name,
        temperature=current_reading.temperature,
        humidity=current_reading.humidity,
        pressure=current_reading.pressure,
        light=current_reading.light,
        anomaly_list=_format_anomaly_list(anomalies),
        trend_context=_format_trend_context(recent_readings),
    )

    try:
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )
        explanation = response.text.strip()
        logger.debug("LLM explanation: %s", explanation)
        return explanation
    except APIError as exc:
        logger.error("Gemini API error during explanation generation: %s", exc)
        return None
