import json
from typing import Any, List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.persona import PersonaProfile
from app.schemas.persona import ExtractedPersonaProfile
from app.services.embedding_service import embedding_service

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
            client_kwargs: dict[str, Any] = {"api_key": settings.OPENAI_API_KEY}
            if settings.OPENAI_BASE_URL:
                client_kwargs["base_url"] = settings.OPENAI_BASE_URL
            self.raw_client = AsyncOpenAI(**client_kwargs)
            self.client = instructor.from_openai(self.raw_client)

    async def generate_response_and_extract(
        self,
        conversation_history: List[dict[str, Any]],
        latest_message: str,
    ) -> Tuple[str, ExtractedPersonaProfile]:
        if settings.OPENAI_API_KEY in {"mock-key", "your-openai-or-mock-api-key"}:
            extracted = ExtractedPersonaProfile(
                lifestyle_summary=f"Discovered habits based on: {latest_message}",
                core_values={"growth": "high", "authenticity": "vital"},
                dealbreakers={"smoking": False, "relocation": "open"},
                is_complete=True,
            )
            return (
                "I have a comprehensive understanding of your persona and core constraints. "
                "Let's find your matches!",
                extracted,
            )

        if self.client is None or self.raw_client is None:
            raise RuntimeError(
                "OpenAI and Instructor dependencies are required for onboarding generation."
            )

        system_prompt = (
            "You are the AuraMatch AI Strategic Persona Architect. Your mission is to uncover "
            "a user's authentic dating persona through a thoughtful, empathetic conversation.\n\n"
            "STRATEGY:\n"
            "1. Ask only ONE targeted question at a time.\n"
            "2. Turn 1 focuses on daily rhythm and work-life lifestyle.\n"
            "3. Turn 2 focuses on core psychological values and connection styles.\n"
            "4. Turn 3 focuses on explicit non-negotiables and dealbreakers.\n"
            "5. Set is_complete=True only after at least 2 lifestyle traits, 2 core values, "
            "and 1 explicit dealbreaker have been gathered.\n\n"
            "Extract whatever data you have discovered so far into the structured schema."
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
            f"You are the AuraMatch AI dating strategist. The user just said: '{latest_message}'.\n"
            f"Extracted profile status:\n"
            f"- Lifestyle: {extracted_data.lifestyle_summary}\n"
            f"- Core Values: {extracted_data.core_values}\n"
            f"- Dealbreakers: {extracted_data.dealbreakers}\n"
            f"- Is Complete: {extracted_data.is_complete}\n\n"
            "If is_complete is false, acknowledge what they said warmly and ask the next "
            "strategic question. If true, thank them and state that the agent is ready to "
            "search and negotiate with candidate agents."
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

        embedding_payload = embedding_service.build_embedding_payload(
            lifestyle_summary=extracted.lifestyle_summary,
            core_values=extracted.core_values,
            dealbreakers=extracted.dealbreakers,
        )
        persona.embedding = await embedding_service.generate_embedding(embedding_payload)

        await db.commit()
        await db.refresh(persona)
        return persona


onboarding_service = OnboardingService()
