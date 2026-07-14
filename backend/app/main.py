"""FastAPI application composition root."""

from fastapi import FastAPI

from backend.app.config.settings import get_settings


def create_app() -> FastAPI:
    """Build the API application without performing network or storage I/O."""

    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Local-first, multi-source knowledge assistant API.",
    )

    @app.get("/health", tags=["system"])
    def health_check() -> dict[str, str]:
        """Provide a lightweight liveness endpoint for local and deployed runtimes."""

        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
