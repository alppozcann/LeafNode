import asyncio
import logging

from google import genai
from google.genai.errors import APIError

from app.config import settings
from app.core.prompts import ANOMALY_EXPLANATION_PROMPT
from app.models.anomaly_record import AnomalyRecord
from app.models.sensor_reading import SensorReading

logger = logging.getLogger(__name__)

# Cache for discovered models
_discovered_models: list[str] = []


async def _get_available_models() -> list[str]:
    """Dynamically discover models that support content generation."""
    global _discovered_models
    if _discovered_models:
        return _discovered_models

    if not settings.GEMINI_API_KEYS:
        logger.warning("No Gemini API keys configured.")
        return settings.GEMINI_FALLBACK_MODELS

    _NON_TEXT = frozenset({
        "tts", "audio", "image", "live", "robotics", "computer-use",
        "embedding", "imagen", "veo", "lyria", "aqa", "nano-banana",
        "deep-research", "customtools",
    })

    for api_key in settings.GEMINI_API_KEYS:
        try:
            logger.info("Discovering available Gemini models...")
            client = genai.Client(api_key=api_key)
            models = await client.aio.models.list()

            valid_models = []
            for m in models:
                name = m.name.split("/")[-1]
                actions = getattr(m, "supported_actions", None) or []
                if "generateContent" not in actions:
                    continue
                if any(kw in name for kw in _NON_TEXT):
                    continue
                valid_models.append(name)

            _discovered_models = valid_models
            logger.info("Discovered %d text-generation models", len(valid_models))
            return _discovered_models
        except Exception as e:
            logger.warning("Failed to discover models with key #%d: %s", settings.GEMINI_API_KEYS.index(api_key) + 1, e)
            continue

    logger.error("All API keys failed model discovery. Using fallback list.")
    return settings.GEMINI_FALLBACK_MODELS


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
            f"humidity={r.humidity}%, pressure={r.pressure} hPa, light={r.light} lux, soil={getattr(r, 'soil_moisture', 0)}%"
        )
    return "\n".join(lines)


async def generate_explanation(
    plant_name: str,
    current_reading: SensorReading,
    anomalies: list[AnomalyRecord],
    recent_readings: list[SensorReading],
    soil_moisture: float = 0.0,
) -> str | None:
    """Call Gemini to produce a plain-English explanation for the detected anomalies.

    Iterates through multiple API keys and fallback models if calls fail.
    """
    prompt = ANOMALY_EXPLANATION_PROMPT.format(
        plant_name=plant_name,
        temperature=current_reading.temperature,
        humidity=current_reading.humidity,
        pressure=current_reading.pressure,
        light=current_reading.light,
        soil_moisture=soil_moisture,
        anomaly_list=_format_anomaly_list(anomalies),
        trend_context=_format_trend_context(recent_readings),
    )

    # Prepare model fallback list
    discovered = await _get_available_models()
    priority_list = [settings.GEMINI_MODEL] + [
        m for m in settings.GEMINI_FALLBACK_MODELS if m != settings.GEMINI_MODEL
    ]
    all_fallbacks = priority_list + [m for m in discovered if m not in priority_list]

    # Iterate through each API key
    for i, api_key in enumerate(settings.GEMINI_API_KEYS):
        client = genai.Client(api_key=api_key)
        logger.info("Attempting explanation with API Key #%d", i + 1)

        # For each key, try the fallback models
        for model_name in all_fallbacks:
            try:
                logger.info("Attempting explanation with model: %s (Key #%d)", model_name, i + 1)
                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    ),
                    timeout=30.0,
                )
                explanation = response.text.strip()
                logger.debug("LLM explanation (%s): %s", model_name, explanation)
                return explanation
            except Exception as exc:
                exc_str = str(exc).lower()
                # If it's a quota/rate limit error, we might want to skip to the next API KEY
                # instead of trying more models on the same exhausted key.
                if "429" in exc_str or "quota" in exc_str or "rate limit" in exc_str:
                    logger.warning(
                        "API Key #%d quota exceeded. Switching to next API key...", i + 1
                    )
                    break # Break the inner model loop, continue to next API key
                
                logger.warning(
                    "Model %s failed on Key #%d: %s. Trying next fallback...",
                    model_name, i + 1, exc
                )
                continue

    logger.error("All Gemini API keys and fallback models failed.")
    return None
