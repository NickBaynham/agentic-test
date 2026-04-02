"""Run the microblog API with Uvicorn using settings from the environment."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    from agentic_test.config import get_settings

    settings = get_settings()
    reload = os.getenv("UVICORN_RELOAD", "false").lower() in ("1", "true", "yes")
    uvicorn.run(
        "agentic_test.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=reload,
    )


if __name__ == "__main__":
    main()
