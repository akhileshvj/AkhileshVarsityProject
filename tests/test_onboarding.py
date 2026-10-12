from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.persona import ExtractedPersonaProfile


@pytest.mark.asyncio
async def test_onboarding_chat_endpoint(async_client):
    test_email = "onboard_user@example.com"
    test_password = "SecurePassword123!"

    await async_client.post(
        "/api/v1/auth/register",
        json={"email": test_email, "password": test_password},
    )

    login_resp = await async_client.post(
        "/api/v1/auth/login",
        data={"username": test_email, "password": test_password},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    mock_extracted = ExtractedPersonaProfile(
        lifestyle_summary="Remote software engineer, values quiet weekends and regular fitness.",
        core_values={"family": "high", "growth": "continuous"},
        dealbreakers={"smoking": False, "relocation": "no"},
        is_complete=True,
    )
    mock_reply = "Understood! Your core preferences and dealbreakers are recorded."

    with patch(
        "app.services.onboarding_service.onboarding_service.generate_response_and_extract",
        new=AsyncMock(return_value=(mock_reply, mock_extracted)),
    ):
        chat_resp = await async_client.post(
            "/api/v1/onboarding/chat",
            headers=headers,
            json={"message": "I am a remote dev who works out and cannot stand smoking."},
        )

        assert chat_resp.status_code == 200
        data = chat_resp.json()
        assert data["reply"] == mock_reply
        assert data["is_completed"] is True
        assert data["current_profile"]["dealbreakers"]["smoking"] is False

    status_resp = await async_client.get("/api/v1/onboarding/status", headers=headers)
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["lifestyle_summary"] == mock_extracted.lifestyle_summary
    assert status_data["dealbreakers"]["smoking"] is False
