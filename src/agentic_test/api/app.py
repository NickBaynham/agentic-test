"""FastAPI application: microblog API with Swagger UI at `/`."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import RedirectResponse
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from agentic_test.api.routes import messages
from agentic_test.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    client = MongoClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=5000,
    )
    app.state.mongo_client = client
    if settings.mongodb_ping_on_startup:
        try:
            client.admin.command("ping")
        except ServerSelectionTimeoutError as e:
            client.close()
            raise RuntimeError(
                f"Could not connect to MongoDB at {settings.mongodb_uri!r}. "
                "Start MongoDB (e.g. `make docker-up`) or set MONGODB_URI."
            ) from e
    yield
    client.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Microblog API",
        description=(
            "Demo microservice that stores short messages in MongoDB. "
            "Interactive documentation is served at this root URL."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    @app.get("/", include_in_schema=False)
    async def root_swagger():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=f"{app.title} — Swagger UI",
        )

    @app.get("/docs", include_in_schema=False)
    async def redirect_docs_to_root():
        return RedirectResponse(url="/", status_code=307)

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    app.include_router(messages.router)
    return app


app = create_app()
