import hashlib
import math
import random
from typing import Iterable, List

from app.core.config import settings

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover - optional dependency
    AsyncOpenAI = None


class EmbeddingService:
    def __init__(self):
        self.client = None
        if AsyncOpenAI is not None and not (
            settings.OPENAI_BASE_URL and "groq.com" in settings.OPENAI_BASE_URL
        ):
            client_kwargs = {"api_key": settings.OPENAI_API_KEY}
            if settings.OPENAI_BASE_URL:
                client_kwargs["base_url"] = settings.OPENAI_BASE_URL
            self.client = AsyncOpenAI(**client_kwargs)

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a normalized vector embedding.
        Falls back to a deterministic mock vector when no real API key is configured.
        """
        if self.client is None or not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY in {
            "mock-key",
            "your-openai-or-mock-api-key",
        }:
            return self._mock_embedding(text)

        try:
            response = await self.client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text,
                dimensions=settings.EMBEDDING_DIMENSIONS,
            )
            embedding = response.data[0].embedding
            return self._normalize_vector(embedding)
        except Exception:
            return self._mock_embedding(text)

    @staticmethod
    def build_embedding_payload(lifestyle_summary: str, core_values: dict, dealbreakers: dict) -> str:
        values_str = ", ".join(f"{key}: {value}" for key, value in core_values.items())
        dealbreakers_str = ", ".join(f"{key}: {value}" for key, value in dealbreakers.items())
        return (
            f"Lifestyle: {lifestyle_summary}. "
            f"Core Values: {values_str}. "
            f"Dealbreakers: {dealbreakers_str}."
        )

    @staticmethod
    def _normalize_vector(vector: Iterable[float]) -> List[float]:
        values = [float(value) for value in vector]
        norm = math.sqrt(sum(value * value for value in values))
        if norm == 0:
            return values
        return [value / norm for value in values]

    @staticmethod
    def _mock_embedding(text: str) -> List[float]:
        rng = random.Random(int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16) % (2**32))
        vector = [rng.uniform(-1.0, 1.0) for _ in range(settings.EMBEDDING_DIMENSIONS)]
        return EmbeddingService._normalize_vector(vector)


embedding_service = EmbeddingService()
