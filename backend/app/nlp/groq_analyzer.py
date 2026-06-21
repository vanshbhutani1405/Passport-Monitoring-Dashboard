
import json
import logging
import re
import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

PASSPORT_CATEGORIES = {
    "passport_renewal",
    "passport_delay",
    "passport_application",
    "passport_appointment",
    "passport_verification",
    "passport_status",
    "passport_lost",
    "passport_general",
    "other",
}

SENTIMENTS = {"positive", "neutral", "negative", "mixed"}


class GroqAnalysisResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    language: str = Field(min_length=1, max_length=20)
    category: str
    sentiment: str
    summary: str = Field(default="", max_length=1000)
    is_gibberish: bool

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in PASSPORT_CATEGORIES:
            logger.warning(f"Unknown category '{value}', remapping to 'other'")
            return "other"
        return normalized

    @field_validator("sentiment")
    @classmethod
    def validate_sentiment(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in SENTIMENTS:
            logger.warning(f"Unknown sentiment '{value}', remapping to 'neutral'")
            return "neutral"
        return normalized

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("summary")
    @classmethod
    def normalize_summary(cls, value: str) -> str:
        return value.strip()


class GroqRateLimitError(Exception):
    """Exception raised when Groq API returns a 429 rate limit error"""
    pass


class GroqAnalyzer:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = None
        self._rate_limit_error_cls = None
        self._api_error_cls = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        if not self.settings.groq_api_key:
            raise ValueError("Groq API key is missing. Set GROQ_API_KEY.")

        try:
            from groq import APIError, Groq, RateLimitError
        except ImportError as exc:
            raise RuntimeError("The groq package is required for NLP analysis.") from exc

        self._api_error_cls = APIError
        self._rate_limit_error_cls = RateLimitError
        self._client = Groq(api_key=self.settings.groq_api_key)
        return self._client

    def analyze(self, content: str) -> GroqAnalysisResult:
        if not content or not content.strip():
            return GroqAnalysisResult(
                language="unknown",
                category="other",
                sentiment="neutral",
                summary="Empty or missing content.",
                is_gibberish=True,
            )

        client = self._get_client()
        retry_delays = [30, 60, 120]  # 30s, 60s, 120s delays for retries
        last_exception = None

        for attempt, delay in enumerate(retry_delays, start=1):
            try:
                response = client.chat.completions.create(
                    model=self.settings.groq_model,
                    temperature=0,
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "system",
                            "content": self._system_prompt(),
                        },
                        {
                            "role": "user",
                            "content": content[:6000],
                        },
                    ],
                )
                raw_content = response.choices[0].message.content
                result = self._parse_response(raw_content)
                return result
            except Exception as exc:
                last_exception = exc
                if self._rate_limit_error_cls and isinstance(exc, self._rate_limit_error_cls):
                    if attempt < len(retry_delays):
                        logger.warning(f"Groq rate limit hit (attempt {attempt}/{len(retry_delays)}), waiting {delay}s before retrying")
                        time.sleep(delay)
                    else:
                        logger.error(f"Groq rate limit hit after {len(retry_delays)} attempts, marking post as rate-limited")
                        raise GroqRateLimitError(f"Rate limit exceeded after {len(retry_delays)} retries") from exc
                else:
                    if self._api_error_cls and isinstance(exc, self._api_error_cls):
                        logger.error(f"Groq API request failed: {str(exc)}")
                    else:
                        logger.error(f"Groq analysis failed: {str(exc)}")
                    raise

        raise last_exception

    @staticmethod
    def _system_prompt() -> str:
        categories = ", ".join(sorted(PASSPORT_CATEGORIES))
        sentiments = ", ".join(sorted(SENTIMENTS))
        return (
            "Analyze passport-related social media text. "
            "Return only valid JSON with exactly these keys: "
            "language, category, sentiment, summary, is_gibberish. "
            f"category must be one of: {categories}. "
            f"sentiment must be one of: {sentiments}. "
            "language should be a short ISO-like language code when possible. "
            "summary must be one concise sentence. "
            "If the text is spam, meaningless, or unreadable, set is_gibberish to true "
            "and use category other."
        )

    def _parse_response(self, raw_content: str | None) -> GroqAnalysisResult:
        if not raw_content:
            raise ValueError("Groq returned an empty response.")

        try:
            payload = json.loads(raw_content)
        except json.JSONDecodeError:
            payload = self._extract_json_object(raw_content)

        try:
            return GroqAnalysisResult.model_validate(payload)
        except ValidationError as exc:
            logger.warning(f"Groq response validation failed: payload={payload}, errors={exc.errors()}")
            raise ValueError("Groq returned an invalid analysis payload.") from exc

    @staticmethod
    def _extract_json_object(raw_content: str) -> dict[str, Any]:
        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_content, re.DOTALL)
        if fenced_match:
            raw_content = fenced_match.group(1)

        object_match = re.search(r"\{.*\}", raw_content, re.DOTALL)
        if not object_match:
            raise ValueError("Groq response did not contain a JSON object.")

        try:
            return json.loads(object_match.group(0))
        except json.JSONDecodeError as exc:
            logger.warning(f"Failed to parse Groq JSON response: {raw_content}")
            raise ValueError("Groq response contained malformed JSON.") from exc

