import uuid
from typing import Any

from pydantic import BaseModel, Field


class DealbreakerCheck(BaseModel):
    category: str
    user_value: str
    is_flexible: bool


class Offer(BaseModel):
    turn_number: int
    topic: str
    proposed_compromise: str
    flexibility_score: float = Field(ge=0.0, le=1.0)


class Evaluation(BaseModel):
    turn_number: int
    accepted: bool
    score: float = Field(ge=0.0, le=100.0)
    reasoning: str
    counter_offer: Offer | None = None


class NegotiationStartRequest(BaseModel):
    target_user_id: uuid.UUID


class NegotiationRead(BaseModel):
    id: uuid.UUID
    initiator_id: uuid.UUID
    target_id: uuid.UUID
    status: str
    compatibility_score: float | None = None
    synthesis_summary: str | None = None
    dialogue_log: list[dict[str, Any]]

    model_config = {"from_attributes": True}
