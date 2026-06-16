from app.core.config import Settings


def test_llm_settings_can_be_configured() -> None:
    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
        jwt_secret_key="test-secret",
        llm_api_key="test-api-key",
        llm_model="gpt-4o-mini",
        llm_base_url="https://api.openai.com/v1",
    )

    assert settings.llm_api_key == "test-api-key"
    assert settings.llm_model == "gpt-4o-mini"
    assert settings.llm_base_url == "https://api.openai.com/v1"


def test_llm_settings_are_optional() -> None:
    settings = Settings(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
        jwt_secret_key="test-secret",
    )

    assert settings.llm_api_key is None
    assert settings.llm_model == "gpt-4o-mini"
    assert settings.llm_base_url is None
