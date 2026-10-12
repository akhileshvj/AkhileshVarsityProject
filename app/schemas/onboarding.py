from typing import Optional

from pydantic import BaseModel

from app.schemas.persona import ExtractedPersonaProfile


class ChatMessage(BaseModel):
    role: str
    content: str


class OnboardingChatRequest(BaseModel):
    message: str


class OnboardingChatResponse(BaseModel):
    reply: str
    is_completed: bool
    current_profile: Optional[ExtractedPersonaProfile] = None
