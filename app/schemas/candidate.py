import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class CandidateRecommendation(BaseModel):
    user_id: uuid.UUID
    lifestyle_summary: Optional[str] = None
    core_values: Dict[str, Any] = Field(default_factory=dict)
    dealbreakers: Dict[str, Any] = Field(default_factory=dict)
    similarity_score: float = Field(
        ...,
        description="Cosine similarity normalized between 0.0 and 1.0 (1.0 = identical)",
    )

    model_config = {"from_attributes": True}


class CandidatePoolResponse(BaseModel):
    total_candidates: int
    candidates: list[CandidateRecommendation]
