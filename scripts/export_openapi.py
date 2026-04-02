#!/usr/bin/env python3
"""Write OpenAPI 3 specs to docs/openapi.json and docs/openapi.yaml (requires PyYAML)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    os.environ.setdefault("MONGODB_PING_ON_STARTUP", "false")

    import mongomock
    import pymongo

    pymongo.MongoClient = mongomock.MongoClient  # type: ignore[misc, assignment]

    from agentic_test.config import clear_settings_cache
    from agentic_test.api.app import create_app

    clear_settings_cache()
    spec = create_app().openapi()

    docs = ROOT / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "openapi.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")

    import yaml

    (docs / "openapi.yaml").write_text(
        yaml.dump(spec, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"Wrote {docs / 'openapi.json'} and {docs / 'openapi.yaml'}")


if __name__ == "__main__":
    main()
