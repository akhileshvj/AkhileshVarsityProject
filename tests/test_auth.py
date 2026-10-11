import uuid

import pytest


@pytest.mark.asyncio
async def test_register_and_login_flow(async_client):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"

    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 201
    assert register_response.json()["email"] == email

    login_response = await async_client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email


@pytest.mark.asyncio
async def test_duplicate_registration_is_rejected(async_client):
    payload = {"email": "duplicate@example.com", "password": "SecurePassword123!"}
    assert (await async_client.post("/api/v1/auth/register", json=payload)).status_code == 201
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
