import uuid

from fastapi.testclient import TestClient


def test_register_user_returns_created_user(client: TestClient) -> None:
    email = f"user-{uuid.uuid4()}@example.com"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "strongpassword123",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["email"] == email
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "hashed_password" not in data


def test_register_user_rejects_duplicate_email(client: TestClient) -> None:
    email = f"user-{uuid.uuid4()}@example.com"

    first_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "strongpassword123",
        },
    )

    second_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "strongpassword123",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {"detail": "Email is already registered"}
