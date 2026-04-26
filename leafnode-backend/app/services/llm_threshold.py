import asyncio
import json
import logging

from google import genai

from app.config import settings
from app.core.prompts import THRESHOLD_GENERATION_PROMPT

logger = logging.getLogger(__name__)


class ThresholdGenerationError(Exception):
    pass


async def generate_thresholds(plant_name: str) -> dict:
    """Call Gemini to generate sensor thresholds for a plant type.

    Tries each configured API key in order; raises ThresholdGenerationError
    if all keys fail.
    """
    if not settings.GEMINI_API_KEYS:
        raise ThresholdGenerationError("No Gemini API keys configured")

    prompt = THRESHOLD_GENERATION_PROMPT.format(plant_name=plant_name)
    last_error: Exception | None = None

    for i, api_key in enumerate(settings.GEMINI_API_KEYS):
        client = genai.Client(api_key=api_key)
        try:
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                ),
                timeout=20.0,
            )
        except asyncio.TimeoutError as exc:
            logger.warning("Gemini API Key #%d timed out during threshold generation", i + 1)
            last_error = exc
            continue
        except Exception as exc:
            logger.warning("Gemini API Key #%d error during threshold generation: %s", i + 1, exc)
            last_error = exc
            continue
        break
    else:
        raise ThresholdGenerationError(f"All Gemini API keys failed: {last_error}") from last_error

    raw = response.text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    logger.debug("LLM threshold raw response: %s", raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse threshold JSON from LLM: %s | raw=%s", exc, raw)
        raise ThresholdGenerationError(f"Invalid JSON from LLM: {raw}") from exc

    required_keys = {"temperature", "humidity", "pressure", "light", "soil_moisture"}
    if not required_keys.issubset(data.keys()):
        raise ThresholdGenerationError(
            f"LLM response missing required keys. Got: {list(data.keys())}"
        )

    return data
