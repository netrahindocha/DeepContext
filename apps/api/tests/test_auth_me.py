from fastapi.testclient import TestClient


def test_me_returns_current_user_for_valid_token(
    client: TestClient,
    register_and_login,
) -> None:
    email, token = register_and_login(client)

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["email"] == email
    assert data["is_active"] is True
    assert "id" in data
    assert "hashed_password" not in data


def test_me_rejects_missing_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_me_rejects_invalid_token(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer not-a-valid-token",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authentication credentials"}
