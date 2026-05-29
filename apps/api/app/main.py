from fastapi import FastAPI
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.modules.health.router import router as health_router

def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.include_router(health_router)

    return app

app = create_app()