import json
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.negotiation import Negotiation
from app.models.persona import PersonaProfile
from app.schemas.negotiation import DealbreakerCheck, Evaluation, Offer

try:
    import instructor
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover - optional live-model dependencies
    instructor = None
    AsyncOpenAI = None


class NegotiationService:
    def __init__(self) -> None:
        self.raw_client = None
        self.client = None
        if AsyncOpenAI is not None and instructor is not None:
            client_kwargs: dict[str, Any] = {"api_key": settings.OPENAI_API_KEY}
            base_url = getattr(settings, "OPENAI_BASE_URL", None)
            if base_url:
                client_kwargs["base_url"] = base_url
            self.raw_client = AsyncOpenAI(**client_kwargs)
            self.client = instructor.from_openai(self.raw_client)

    async def execute_negotiation(
        self,
        db: AsyncSession,
        initiator_id: uuid.UUID,
        target_id: uuid.UUID,
    ) -> Negotiation:
        profiles = (
            await db.execute(
                select(PersonaProfile).where(
                    PersonaProfile.user_id.in_([initiator_id, target_id])
                )
            )
        ).scalars().all()
        by_user_id = {profile.user_id: profile for profile in profiles}
        initiator = by_user_id.get(initiator_id)
        target = by_user_id.get(target_id)
        if initiator is None or target is None:
            raise ValueError("Both users must have completed persona profiles before negotiating.")

        if self.client is None or self.raw_client is None or settings.OPENAI_API_KEY in {
            "mock-key",
            "your-openai-or-mock-api-key",
        }:
            return await self._execute_mock(db, initiator, target)

        dialogue_log: list[dict[str, Any]] = []
        check: DealbreakerCheck = await self.client.chat.completions.create(
            model=settings.LLM_MODEL,
            response_model=DealbreakerCheck,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Agent 1 dealbreakers: {json.dumps(initiator.dealbreakers)}\n"
                        f"Agent 2 dealbreakers: {json.dumps(target.dealbreakers)}\n"
                        "Identify any strict conflict."
                    ),
                }
            ],
            temperature=0.1,
        )
        dialogue_log.append({"turn": 1, "type": "DealbreakerCheck", "payload": check.model_dump()})

        offer: Offer = await self.client.chat.completions.create(
            model=settings.LLM_MODEL,
            response_model=Offer,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Profiles: {initiator.lifestyle_summary}; {target.lifestyle_summary}\n"
                        "Propose a practical shared-lifestyle compromise."
                    ),
                }
            ],
            temperature=0.3,
        )
        dialogue_log.append({"turn": 2, "type": "Offer", "payload": offer.model_dump()})

        evaluation: Evaluation = await self.client.chat.completions.create(
            model=settings.LLM_MODEL,
            response_model=Evaluation,
            messages=[
                {
                    "role": "user",
                    "content": f"Evaluate this compatibility offer from 0 to 100: {offer.model_dump()}",
                }
            ],
            temperature=0.2,
        )
        dialogue_log.append({"turn": 3, "type": "Evaluation", "payload": evaluation.model_dump()})

        summary_response = await self.raw_client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "Summarize this matchmaking negotiation in two sentences."},
                {"role": "user", "content": json.dumps(dialogue_log)},
            ],
            temperature=0.5,
            max_tokens=150,
        )
        summary = summary_response.choices[0].message.content or "Negotiation completed."
        negotiation = Negotiation(
            initiator_id=initiator_id,
            target_id=target_id,
            status="SUCCESS" if evaluation.accepted else "REJECTED",
            compatibility_score=evaluation.score,
            synthesis_summary=summary,
            dialogue_log=dialogue_log,
        )
        db.add(negotiation)
        await db.commit()
        await db.refresh(negotiation)
        return negotiation

    async def _execute_mock(
        self, db: AsyncSession, initiator: PersonaProfile, target: PersonaProfile
    ) -> Negotiation:
        compatible = initiator.dealbreakers.get("smoking") == target.dealbreakers.get("smoking")
        score = 88.5 if compatible else 32.0
        summary = (
            "Both agents found strong alignment on daily work-life rhythms and non-smoking habits."
            if compatible
            else "Negotiation collapsed on Turn 1 due to a strict smoking dealbreaker conflict."
        )
        dialogue_log = [
            {
                "turn": 1,
                "type": "DealbreakerCheck",
                "content": {"status": "PASSED" if compatible else "FAILED", "category": "smoking"},
            },
            {
                "turn": 2,
                "type": "Evaluation",
                "content": {"score": score, "accepted": compatible, "summary": summary},
            },
        ]
        negotiation = Negotiation(
            initiator_id=initiator.user_id,
            target_id=target.user_id,
            status="SUCCESS" if compatible else "REJECTED",
            compatibility_score=score,
            synthesis_summary=summary,
            dialogue_log=dialogue_log,
        )
        db.add(negotiation)
        await db.commit()
        await db.refresh(negotiation)
        return negotiation


negotiation_service = NegotiationService()
