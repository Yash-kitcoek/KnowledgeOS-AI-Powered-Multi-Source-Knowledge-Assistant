"""FastAPI application composition root."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.routers.ingestion import router as ingestion_router
from backend.app.api.routers.knowledge import router as knowledge_router
from backend.app.config.settings import get_settings
from backend.app.database.repository import KnowledgeRepository


def create_app() -> FastAPI:
    """Build the API application without performing network or storage I/O."""

    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Local-first, multi-source knowledge assistant API.",
    )
    app.include_router(ingestion_router)
    app.include_router(knowledge_router)
    KnowledgeRepository(settings.database_path).initialize()

    static_directory = Path(__file__).parent / "web"
    app.mount("/static", StaticFiles(directory=static_directory), name="static")

    @app.get("/", include_in_schema=False)
    def web_app() -> FileResponse:
        return FileResponse(static_directory / "index.html")

    @app.get("/health", tags=["system"])
    def health_check() -> dict[str, str]:
        """Provide a lightweight liveness endpoint for local and deployed runtimes."""

        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
