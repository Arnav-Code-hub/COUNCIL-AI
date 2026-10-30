"""Bounded, tool-free Gemini reviews. Live enablement is gated by Settings."""

import json
import random
import ssl
import time
from pathlib import Path

import httpx
from google import genai
from google.genai import errors, types

from council.engine import validate_references
from council.schemas import REVIEWERS, Evidence, ReviewerReport

PROMPTS = Path(__file__).parent / "prompts"
MAX_OUTPUT_CHARACTERS = 100000
MAX_INPUT_CHARACTERS = 1000000
TRANSIENT_CODES = {408, 429, 500, 502, 503, 504}
# An overloaded or rate-limited model rarely recovers within a second, so the
# single permitted retry waits longer, honouring the provider's own hint.
RETRY_BASE_SECONDS = 5.0
RETRY_MAX_SECONDS = 30.0


def _retry_delay(exc, jitter: float) -> float:
    """Seconds before the one retry: the provider's RetryInfo hint or a base
    backoff, capped, plus up to 25% random jitter (jitter is in [0, 1))."""
    delay = RETRY_BASE_SECONDS
    body = getattr(exc, "details", None)
    details = body.get("error", {}).get("details", []) if isinstance(body, dict) else []
    for detail in details if isinstance(details, list) else []:
        hint = detail.get("retryDelay") if isinstance(detail, dict) else None
        if isinstance(hint, str) and hint.endswith("s"):
            try:
                delay = max(delay, float(hint[:-1]))
            except ValueError:
                pass
    delay = min(delay, RETRY_MAX_SECONDS)
    return delay + delay * 0.25 * jitter


def _without_array_maxima(value):
    # Nested maxima exceed Gemini's schema complexity limit; Pydantic still enforces them.
    if isinstance(value, dict):
        return {k: _without_array_maxima(v) for k, v in value.items() if k != "maxItems"}
    if isinstance(value, list):
        return [_without_array_maxima(v) for v in value]
    return value


class GeminiReviewer:
    simulated = False

    def __init__(
        self, settings, *, client_factory=genai.Client, sleep=time.sleep, jitter=random.random
    ):
        self.model = settings.gemini_model
        self._key = settings.gemini_key.get_secret_value()
        if not self.model or not self._key:
            raise ValueError("An explicit Gemini model and API key are required.")
        self._timeout = settings.timeout_seconds * 1000
        self._client_factory = client_factory
        self._sleep = sleep
        self._jitter = jitter

    def review(self, reviewer: str, inventory: list[Evidence]) -> ReviewerReport:
        if reviewer not in REVIEWERS:
            raise ValueError("Unknown council reviewer.")
        instruction = (PROMPTS / "common.txt").read_text(encoding="utf-8")
        instruction += "\n\n" + (PROMPTS / f"{reviewer}.txt").read_text(encoding="utf-8")
        instruction += f"\nReturn reviewer exactly as {json.dumps(reviewer)}."
        content = json.dumps(
            {
                "evidence": [
                    {
                        "id": item.id,
                        "name": item.name,
                        "sha256": item.sha256,
                        "lines": [
                            {"number": index, "text": line}
                            for index, line in enumerate(item.lines, 1)
                        ],
                    }
                    for item in inventory
                ]
            },
            ensure_ascii=False,
        )
        if len(content) > MAX_INPUT_CHARACTERS:
            raise ValueError(
                "Numbered evidence exceeds model input limit; reduce supplied evidence."
            )
        config = types.GenerateContentConfig(
            system_instruction=instruction,
            response_mime_type="application/json",
            response_json_schema=_without_array_maxima(ReviewerReport.model_json_schema()),
            max_output_tokens=6144,
            tools=[],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        # SDK retries are off so one transient retry cannot multiply into hidden paid calls.
        options = types.HttpOptions(
            timeout=self._timeout,
            retry_options=types.HttpRetryOptions(attempts=1),
            client_args={"verify": ssl.create_default_context()},
        )
        with self._client_factory(api_key=self._key, http_options=options) as client:
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=self.model, contents=content, config=config
                    )
                    break
                except (httpx.TransportError, errors.APIError) as exc:
                    transient = (
                        isinstance(exc, httpx.TransportError)
                        or getattr(exc, "code", None) in TRANSIENT_CODES
                    )
                    if attempt or not transient:
                        raise
                    self._sleep(_retry_delay(exc, self._jitter()))
        raw = response.text
        if not isinstance(raw, str) or not raw.strip() or len(raw) > MAX_OUTPUT_CHARACTERS:
            raise ValueError("Gemini returned empty or oversized reviewer output.")
        result = ReviewerReport.model_validate_json(raw)
        if result.reviewer != reviewer:
            raise ValueError("Reviewer identity mismatch.")
        validate_references(result, inventory)
        return result
