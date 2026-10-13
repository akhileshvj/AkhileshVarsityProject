import math
import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.persona import PersonaProfile
from app.schemas.candidate import CandidateRecommendation


class CandidateService:
    @staticmethod
    def _coerce_embedding(raw_embedding) -> list[float] | None:
        if raw_embedding is None:
            return None
        if isinstance(raw_embedding, list):
            return [float(value) for value in raw_embedding]
        if isinstance(raw_embedding, tuple):
            return [float(value) for value in raw_embedding]
        if isinstance(raw_embedding, str):
            try:
                return [float(value) for value in raw_embedding.split(",")]
            except ValueError:
                return None
        return None

    @staticmethod
    def _normalize_embedding(values: list[float]) -> list[float]:
        norm = math.sqrt(sum(value * value for value in values))
        if norm == 0:
            return values
        return [value / norm for value in values]

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if len(left) != len(right):
            return 0.0

        dot = sum(a * b for a, b in zip(left, right))
        return max(0.0, min(1.0, dot))

    async def get_top_candidates(
        self,
        db: AsyncSession,
        current_user_id: uuid.UUID,
        limit: int = 5,
    ) -> List[CandidateRecommendation]:
        stmt = select(PersonaProfile).where(PersonaProfile.user_id == current_user_id)
        current_persona = (await db.execute(stmt)).scalar_one_or_none()

        if current_persona is None or current_persona.embedding is None:
            return []

        current_embedding = self._coerce_embedding(current_persona.embedding)
        if current_embedding is None:
            return []

        current_embedding = self._normalize_embedding(current_embedding)

        stmt = select(PersonaProfile).where(
            PersonaProfile.user_id != current_user_id,
            PersonaProfile.embedding.isnot(None),
        )
        personas = (await db.execute(stmt)).scalars().all()

        recommendations: list[CandidateRecommendation] = []
        for persona in personas:
            candidate_embedding = self._coerce_embedding(persona.embedding)
            if candidate_embedding is None:
                continue

            candidate_embedding = self._normalize_embedding(candidate_embedding)
            similarity = self._cosine_similarity(current_embedding, candidate_embedding)
            recommendations.append(
                CandidateRecommendation(
                    user_id=persona.user_id,
                    lifestyle_summary=persona.lifestyle_summary,
                    core_values=persona.core_values,
                    dealbreakers=persona.dealbreakers,
                    similarity_score=round(similarity, 4),
                )
            )

        recommendations.sort(key=lambda item: item.similarity_score, reverse=True)
        return recommendations[:limit]


candidate_service = CandidateService()
