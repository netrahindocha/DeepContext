from fastapi import FastAPI
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.modules.health.router import router as health_router
from app.modules.auth.router import router as auth_router
from app.modules.documents.router import router as documents_router
from app.modules.workspaces.router import router as workspaces_router
from app.modules.chat.router import router as chat_router


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(workspaces_router)
    app.include_router(documents_router)
    app.include_router(chat_router)
    return app


app = create_app()
