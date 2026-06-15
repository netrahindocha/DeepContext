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


def test_register_user_rejects_duplicate_email_with_different_casing(
    client: TestClient,
) -> None:
    unique_id = uuid.uuid4()
    first_email = f"User-{unique_id}@Example.com"
    second_email = f"user-{unique_id}@example.com"

    first_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": first_email,
            "password": "strongpassword123",
        },
    )

    second_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": second_email,
            "password": "strongpassword123",
        },
    )

    assert first_response.status_code == 201
    assert first_response.json()["email"] == first_email.lower()
    assert second_response.status_code == 409
    assert second_response.json() == {"detail": "Email is already registered"}


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
