from app.db.session import AsyncSessionLocal, engine


def test_database_session_objects_are_configured() -> None:
    assert engine is not None
    assert AsyncSessionLocal is not None
