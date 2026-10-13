import uuid

import pytest

from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token, get_password_hash
from app.models.persona import PersonaProfile
from app.models.user import User
from app.services.embedding_service import embedding_service


@pytest.mark.asyncio
async def test_candidate_recommendations_flow(async_client):
    async with AsyncSessionLocal() as session:
        user_main = User(
            email=f"main_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password=get_password_hash("pass123"),
        )
        session.add(user_main)
        await session.flush()

        vec_main = await embedding_service.generate_embedding(
            "Athletic remote tech lead loving nature and quiet evenings"
        )
        persona_main = PersonaProfile(
            user_id=user_main.id,
            lifestyle_summary="Athletic remote tech lead",
            core_values={"growth": "high"},
            dealbreakers={"smoking": False},
            embedding=vec_main,
        )
        session.add(persona_main)

        user_match = User(
            email=f"candidate_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password=get_password_hash("pass123"),
        )
        session.add(user_match)
        await session.flush()

        vec_candidate = await embedding_service.generate_embedding(
            "Outdoor enthusiast and software designer who enjoys trails"
        )
        persona_match = PersonaProfile(
            user_id=user_match.id,
            lifestyle_summary="Outdoor enthusiast and software designer",
            core_values={"growth": "high"},
            dealbreakers={"smoking": False},
            embedding=vec_candidate,
        )
        session.add(persona_match)
        await session.commit()

        token = create_access_token(subject=user_main.id)

    response = await async_client.get(
        "/api/v1/candidates/recommendations?limit=3",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_candidates"] >= 1
    assert data["candidates"][0]["similarity_score"] > 0.0
    assert str(data["candidates"][0]["user_id"]) != str(user_main.id)
