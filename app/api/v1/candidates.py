from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.candidate import CandidatePoolResponse
from app.services.candidate_service import candidate_service

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.get("/recommendations", response_model=CandidatePoolResponse)
async def get_candidate_recommendations(
    limit: int = Query(default=5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    candidates = await candidate_service.get_top_candidates(
        db=db,
        current_user_id=current_user.id,
        limit=limit,
    )
    return CandidatePoolResponse(
        total_candidates=len(candidates),
        candidates=candidates,
    )
