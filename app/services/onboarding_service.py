import json
from typing import Any, List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.persona import PersonaProfile
from app.schemas.persona import ExtractedPersonaProfile

try:
    from openai import AsyncOpenAI
    import instructor
except ImportError:  # pragma: no cover - optional dependency for local/dev environments
    AsyncOpenAI = None
    instructor = None


class OnboardingService:
    def __init__(self):
        self.raw_client = None
        self.client = None
        if AsyncOpenAI is not None and instructor is not None:
            self.raw_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.client = instructor.from_openai(self.raw_client)

    async def generate_response_and_extract(
        self,
        conversation_history: List[dict[str, Any]],
        latest_message: str,
    ) -> Tuple[str, ExtractedPersonaProfile]:
        if self.client is None or self.raw_client is None:
            raise RuntimeError(
                "OpenAI and Instructor dependencies are required for onboarding generation."
            )

        system_prompt = (
            "You are the AuraMatch AI Onboarding Specialist. Your purpose is to uncover "
            "the user's core lifestyle habits, deep values, and absolute non-negotiables / dealbreakers.\n"
            "Be empathetic, perceptive, and concise. Ask targeted follow-up questions.\n"
            "Extract all gathered insights into the structured schema.\n"
            "Mark is_complete=True ONLY when at least 2 core values, 2 lifestyle traits, "
            "and 1 explicit dealbreaker have been identified."
        )

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": latest_message})

        extracted_data: ExtractedPersonaProfile = await self.client.chat.completions.create(
            model=settings.LLM_MODEL,
            response_model=ExtractedPersonaProfile,
            messages=messages,
            temperature=0.2,
        )

        reply_prompt = (
            f"Given the user's latest message and our extracted understanding:\n"
            f"Summary: {extracted_data.lifestyle_summary}\n"
            f"Core Values: {json.dumps(extracted_data.core_values)}\n"
            f"Dealbreakers: {json.dumps(extracted_data.dealbreakers)}\n"
            f"Is Complete: {extracted_data.is_complete}\n\n"
            "Generate a warm, engaging conversational reply (1-2 sentences). "
            "If is_complete is True, warmly announce that their persona profile is ready. "
            "Otherwise, ask the next relevant question."
        )

        response = await self.raw_client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": reply_prompt},
            ],
            temperature=0.7,
            max_tokens=150,
        )
        assistant_reply = response.choices[0].message.content or "Thanks! I have your profile summary."

        return assistant_reply, extracted_data

    async def save_profile(
        self,
        db: AsyncSession,
        user_id,
        extracted: ExtractedPersonaProfile,
    ) -> PersonaProfile:
        stmt = select(PersonaProfile).where(PersonaProfile.user_id == user_id)
        result = await db.execute(stmt)
        persona = result.scalar_one_or_none()

        if not persona:
            persona = PersonaProfile(user_id=user_id)
            db.add(persona)

        persona.lifestyle_summary = extracted.lifestyle_summary
        persona.core_values = extracted.core_values
        persona.dealbreakers = extracted.dealbreakers

        await db.commit()
        await db.refresh(persona)
        return persona


onboarding_service = OnboardingService()
