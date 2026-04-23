import logging

from google import genai
from google.genai.errors import APIError

from app.config import settings
from app.core.prompts import ANOMALY_EXPLANATION_PROMPT
from app.models.anomaly_record import AnomalyRecord
from app.models.sensor_reading import SensorReading

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Cache for discovered models
_discovered_models: list[str] = []


async def _get_available_models() -> list[str]:
    """Dynamically discover models that support content generation."""
    global _discovered_models
    if _discovered_models:
        return _discovered_models

    try:
        logger.info("Discovering available Gemini models...")
        # Note: In google-genai SDK, list_models is used to find available models
        models = await client.aio.models.list()
        
        # Filter for models that support generating content
        # The SDK returns model objects with name and supported_methods
        valid_models = []
        for m in models:
            # Strip 'models/' prefix if present
            name = m.name.split("/")[-1]
            
            # Check for supported methods if available in the SDK response
            # Usually we look for 'generateContent'
            if hasattr(m, 'supported_generation_methods'):
                 if 'generateContent' in m.supported_generation_methods:
                     valid_models.append(name)
            else:
                # If no methods info, assume standard models are okay
                if "gemini" in name.lower() or "gemma" in name.lower():
                    valid_models.append(name)

        _discovered_models = valid_models
        logger.info("Discovered %d models supporting generation", len(valid_models))
        return _discovered_models
    except Exception as e:
        logger.error("Failed to discover models: %s", e)
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

    Iterates through fallback models if the initial call fails due to quota or other errors.
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

    # 1. Start with the configured primary model
    # 2. Add hardcoded fallbacks from settings
    # 3. Add dynamically discovered models as a last resort
    
    discovered = await _get_available_models()
    
    priority_list = [settings.GEMINI_MODEL] + [
        m for m in settings.GEMINI_FALLBACK_MODELS if m != settings.GEMINI_MODEL
    ]
    
    # Final list: priority models first, then any other discovered ones
    all_fallbacks = priority_list + [m for m in discovered if m not in priority_list]

    for model_name in all_fallbacks:
        try:
            logger.info("Attempting explanation generation with model: %s", model_name)
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            explanation = response.text.strip()
            logger.debug("LLM explanation (%s): %s", model_name, explanation)
            return explanation
        except Exception as exc:
            logger.warning(
                "Model %s failed: %s. Trying next fallback...",
                model_name,
                exc,
            )
            continue

    logger.error("All Gemini fallback models (including discovered ones) failed.")
    return None
