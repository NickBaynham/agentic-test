"""Application entry: loads `.env` from the project root and runs the CLI."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def _project_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def load_environment() -> None:
    """Load variables from `.env` in the project root (if present)."""
    env_path = _project_root() / ".env"
    load_dotenv(env_path, override=False)


def main() -> None:
    load_environment()
    app_env = os.getenv("APP_ENV", "development")
    debug = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")
    print(f"agentic-test starting (APP_ENV={app_env!r}, DEBUG={debug})")
    sys.exit(0)


if __name__ == "__main__":
    main()
