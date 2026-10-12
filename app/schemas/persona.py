import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ExtractedPersonaProfile(BaseModel):
    lifestyle_summary: str = Field(
        ...,
        description="A qualitative summary of the user's daily habits, work-life rhythm, and personality.",
    )
    core_values: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured key-values for deep priorities (e.g., family, ambition, spirituality, communication).",
    )
    dealbreakers: Dict[str, Any] = Field(
        default_factory=dict,
        description="Strict non-negotiable constraints (e.g., smoking: false, relocation: never, kids: wants).",
    )
    is_complete: bool = Field(
        default=False,
        description="Whether enough data has been collected to finalize the discovery process.",
    )


class PersonaProfileRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    lifestyle_summary: Optional[str] = None
    core_values: Dict[str, Any]
    dealbreakers: Dict[str, Any]

    model_config = {"from_attributes": True}
