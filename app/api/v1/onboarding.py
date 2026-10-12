from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.persona import PersonaProfile
from app.models.user import User
from app.schemas.onboarding import OnboardingChatRequest, OnboardingChatResponse
from app.schemas.persona import PersonaProfileRead
from app.services.onboarding_service import onboarding_service

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.post("/chat", response_model=OnboardingChatResponse)
async def process_onboarding_turn(
    req: OnboardingChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        reply, extracted = await onboarding_service.generate_response_and_extract(
            conversation_history=[],
            latest_message=req.message,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Persona extraction failed: {str(exc)}",
        ) from exc

    await onboarding_service.save_profile(db=db, user_id=current_user.id, extracted=extracted)

    return OnboardingChatResponse(
        reply=reply,
        is_completed=extracted.is_complete,
        current_profile=extracted,
    )


@router.get("/status", response_model=PersonaProfileRead)
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PersonaProfile).where(PersonaProfile.user_id == current_user.id)
    persona = (await db.execute(stmt)).scalar_one_or_none()

    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona profile not initialized for this user.",
        )
    return persona
