import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.negotiation import Negotiation
from app.models.user import User
from app.schemas.negotiation import NegotiationRead, NegotiationStartRequest
from app.services.negotiation_service import negotiation_service

router = APIRouter(prefix="/negotiations", tags=["A2A Negotiations"])


@router.post("/start", response_model=NegotiationRead, status_code=status.HTTP_201_CREATED)
async def start_negotiation(
    request: NegotiationStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Negotiation:
    if request.target_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot negotiate with your own persona agent.")
    try:
        return await negotiation_service.execute_negotiation(
            db=db, initiator_id=current_user.id, target_id=request.target_user_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/history", response_model=list[NegotiationRead])
async def list_negotiations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Negotiation]:
    statement = (
        select(Negotiation)
        .where(or_(Negotiation.initiator_id == current_user.id, Negotiation.target_id == current_user.id))
        .order_by(Negotiation.created_at.desc())
    )
    return list((await db.execute(statement)).scalars().all())


@router.get("/{negotiation_id}", response_model=NegotiationRead)
async def get_negotiation(
    negotiation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Negotiation:
    negotiation = (
        await db.execute(select(Negotiation).where(Negotiation.id == negotiation_id))
    ).scalar_one_or_none()
    if negotiation is None:
        raise HTTPException(status_code=404, detail="Negotiation session not found.")
    if current_user.id not in {negotiation.initiator_id, negotiation.target_id}:
        raise HTTPException(status_code=403, detail="Forbidden: You were not part of this negotiation.")
    return negotiation
