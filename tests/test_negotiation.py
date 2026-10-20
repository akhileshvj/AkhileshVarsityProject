import uuid

import pytest

from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token, get_password_hash
from app.models.persona import PersonaProfile
from app.models.user import User


@pytest.mark.asyncio
async def test_negotiation_flow(async_client):
    async with AsyncSessionLocal() as session:
        initiator = User(
            email=f"initiator_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password=get_password_hash("SecurePassword123!"),
        )
        target = User(
            email=f"target_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password=get_password_hash("SecurePassword123!"),
        )
        session.add_all([initiator, target])
        await session.flush()
        session.add_all(
            [
                PersonaProfile(
                    user_id=initiator.id,
                    lifestyle_summary="Runner",
                    core_values={"vitality": "high"},
                    dealbreakers={"smoking": False},
                ),
                PersonaProfile(
                    user_id=target.id,
                    lifestyle_summary="Hiker",
                    core_values={"vitality": "high"},
                    dealbreakers={"smoking": False},
                ),
            ]
        )
        await session.commit()
        token = create_access_token(initiator.id)
        target_id = target.id

    response = await async_client.post(
        "/api/v1/negotiations/start",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_user_id": str(target_id)},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["compatibility_score"] == 88.5
    assert len(data["dialogue_log"]) >= 1

    details = await async_client.get(
        f"/api/v1/negotiations/{data['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert details.status_code == 200
