import json
import logging

from google import genai
from google.genai.errors import APIError

from app.config import settings
from app.core.prompts import THRESHOLD_GENERATION_PROMPT

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.GEMINI_API_KEY)


class ThresholdGenerationError(Exception):
    pass


async def generate_thresholds(plant_name: str) -> dict:
    """Call Gemini to generate sensor thresholds for a plant type.

    Returns a dict with keys: temperature, humidity, pressure, light,
    each containing {min, max}.
    """
    prompt = THRESHOLD_GENERATION_PROMPT.format(plant_name=plant_name)

    try:
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )
    except APIError as exc:
        logger.error("Gemini API error during threshold generation: %s", exc)
        raise ThresholdGenerationError(str(exc)) from exc

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

    required_keys = {"temperature", "humidity", "pressure", "light"}
    if not required_keys.issubset(data.keys()):
        raise ThresholdGenerationError(
            f"LLM response missing required keys. Got: {list(data.keys())}"
        )

    return data
