"""
Tests for app/services/llm_threshold.py

generate_thresholds() parses a JSON blob from Gemini — high risk because
a malformed response propagates silently to PlantProfile creation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.llm_threshold import generate_thresholds, ThresholdGenerationError

VALID_JSON = """{
    "temperature":   {"min": 18, "max": 28},
    "humidity":      {"min": 40, "max": 80},
    "pressure":      {"min": 1000, "max": 1030},
    "light":         {"min": 200, "max": 2000},
    "soil_moisture": {"min": 30,  "max": 70}
}"""


def _resp(text: str) -> MagicMock:
    r = MagicMock()
    r.text = text
    return r


_PATCH = "app.services.llm_threshold.client.aio.models.generate_content"


class TestGenerateThresholds:
    async def test_valid_json_returns_complete_dict(self):
        with patch(_PATCH, new_callable=AsyncMock, return_value=_resp(VALID_JSON)):
            result = await generate_thresholds("Basil")

        assert result["temperature"]["min"] == 18
        assert result["temperature"]["max"] == 28
        assert set(result.keys()) == {"temperature", "humidity", "pressure", "light", "soil_moisture"}

    async def test_markdown_fenced_json_is_unwrapped(self):
        fenced = f"```json\n{VALID_JSON}\n```"
        with patch(_PATCH, new_callable=AsyncMock, return_value=_resp(fenced)):
            result = await generate_thresholds("Basil")

        assert "temperature" in result

    async def test_plain_code_fence_without_language_tag_is_unwrapped(self):
        fenced = f"```\n{VALID_JSON}\n```"
        with patch(_PATCH, new_callable=AsyncMock, return_value=_resp(fenced)):
            result = await generate_thresholds("Basil")

        assert "humidity" in result

    async def test_missing_required_key_raises_threshold_error(self):
        # Response has only one key — four are missing.
        partial = '{"temperature": {"min": 18, "max": 28}}'
        with patch(_PATCH, new_callable=AsyncMock, return_value=_resp(partial)):
            with pytest.raises(ThresholdGenerationError, match="missing required keys"):
                await generate_thresholds("Basil")

    async def test_invalid_json_raises_threshold_error(self):
        with patch(_PATCH, new_callable=AsyncMock, return_value=_resp("not json {{")):
            with pytest.raises(ThresholdGenerationError, match="Invalid JSON"):
                await generate_thresholds("Basil")

    async def test_empty_response_raises_threshold_error(self):
        with patch(_PATCH, new_callable=AsyncMock, return_value=_resp("")):
            with pytest.raises(ThresholdGenerationError):
                await generate_thresholds("Basil")

    async def test_gemini_api_error_raises_threshold_error(self):
        from google.genai.errors import APIError

        try:
            exc = APIError(message="rate limit exceeded")
        except TypeError:
            # If the constructor signature differs in the installed SDK version,
            # create via __new__ to avoid depending on exact constructor args.
            exc = APIError.__new__(APIError)
            exc.args = ("rate limit exceeded",)

        with patch(_PATCH, new_callable=AsyncMock, side_effect=exc):
            with pytest.raises(ThresholdGenerationError):
                await generate_thresholds("Basil")

    async def test_plant_name_is_injected_into_prompt(self):
        """Verify the prompt actually receives the plant name (smoke test)."""
        captured = {}

        async def fake_generate(model, contents):
            captured["contents"] = contents
            return _resp(VALID_JSON)

        with patch(_PATCH, side_effect=fake_generate):
            await generate_thresholds("Monstera")

        assert "Monstera" in captured["contents"]
