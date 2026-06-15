import uuid

from fastapi.testclient import TestClient


def test_login_returns_access_token_for_valid_credentials(client: TestClient) -> None:
    email = f"user-{uuid.uuid4()}@example.com"
    password = "strongpassword123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200
    data = login_response.json()

    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert data["access_token"]


def test_login_accepts_email_with_different_casing(client: TestClient) -> None:
    unique_id = uuid.uuid4()
    registered_email = f"user-{unique_id}@example.com"
    login_email = f"User-{unique_id}@Example.com"
    password = "strongpassword123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": registered_email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": login_email,
            "password": password,
        },
    )

    assert login_response.status_code == 200
    assert login_response.json()["access_token"]


def test_login_rejects_wrong_password(client: TestClient) -> None:
    email = f"user-{uuid.uuid4()}@example.com"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "strongpassword123",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "wrongpassword123",
        },
    )

    assert login_response.status_code == 401
    assert login_response.json() == {"detail": "Invalid email or password"}


def test_login_rejects_unknown_email(client: TestClient) -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": f"missing-{uuid.uuid4()}@example.com",
            "password": "strongpassword123",
        },
    )

    assert login_response.status_code == 401
    assert login_response.json() == {"detail": "Invalid email or password"}
