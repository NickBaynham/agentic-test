# Changelog

All notable changes to this project are documented in this file. The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] — 2026-04-02

### Added (MCP AI API testing harness)

- **`agentic_test.ai_api_tester`**: MCP server ([FastMCP](https://github.com/modelcontextprotocol/python-sdk) / `mcp`) exposing allow-listed tools for introspection, sandboxed workspace I/O under `generated/`, deterministic **Playwright sync `APIRequestContext`** test generation, **pytest** execution with JUnit + **pytest-json-report**, structured summaries, and **Docker Compose** `mongo` / `full` profiles only ([`docker_manager.py`](src/agentic_test/ai_api_tester/docker_manager.py)).
- **Entry point:** `pdm run agentic-mcp-server` / `make mcp`.
- **Tooling:** Ruff + mypy (strict) configuration in `pyproject.toml`; `make lint`, `make typecheck`, `make test` (with coverage on the harness package), `make playwright-py-install` for Python Playwright binaries.
- **Tests:** [`tests/ai_api_tester/`](tests/ai_api_tester/) (sandbox, parser, runner, Docker mocks, MCP app smoke, HTTPServer integration).
- **Docs:** README sections for developers, QA, and AI agents; [`prompts/playwright_api_test_generation.md`](prompts/playwright_api_test_generation.md); [`docs/mcp-testing-guide.md`](docs/mcp-testing-guide.md) (MCP setup, test design, execution, troubleshooting).
- **Handwritten API tests:** [`tests/handwritten_api/`](tests/handwritten_api/) (skipped unless `API_BASE_URL` is set).

### Added (Playwright)

- **[Playwright](https://playwright.dev/)** API test package under [`playwright/`](playwright/) ([`@playwright/test`](https://www.npmjs.com/package/@playwright/test)), with [`playwright/tests/api/messages.spec.ts`](playwright/tests/api/messages.spec.ts) covering health, Swagger, OpenAPI, CRUD, list/sort/pagination, validation, and 404 behavior against a **live** stack.
- **[`scripts/run-api-for-playwright.sh`](scripts/run-api-for-playwright.sh)** — brings up Compose **MongoDB**, waits for `mongosh` ping, then runs Uvicorn on **`127.0.0.1:${PLAYWRIGHT_API_PORT:-18080}`** for Playwright’s `webServer`.
- **Make targets**: `playwright-install`, `playwright-test`; **`make clean`** also removes `playwright/test-results` and `playwright/playwright-report`.
- **Docs**: README prerequisites, onboarding step, Make table, configuration table, and this changelog entry.

### Added

- **Microblog REST API** ([FastAPI](https://fastapi.tiangolo.com/)) storing messages in **MongoDB** via [PyMongo](https://pymongo.readthedocs.io/).
- **Message model** (per document): MongoDB `ObjectId` exposed as string `id`, `author_first_name`, `author_last_name`, `author_email`, `text` (1–255 characters), `created_at`, `updated_at` (UTC).
- **HTTP interface**:
  - `POST /messages` — create a message
  - `GET /messages/{id}` — fetch by id
  - `GET /messages` — list with `skip`, `limit` (max 100), `sort_by` (`created_at` | `updated_at`), `sort_order` (`asc` | `desc`)
  - `PATCH /messages/{id}` — partial update
  - `DELETE /messages/{id}` — delete
  - `GET /health` — liveness
- **Swagger UI** served at **`/`** (root); machine-readable **OpenAPI 3** at `/openapi.json`; **ReDoc** at `/redoc`. Static copies: [docs/openapi.yaml](docs/openapi.yaml) and [docs/openapi.json](docs/openapi.json) (regenerate with `make openapi-export`).
- **Configuration** via environment variables and `.env` ([pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)): `MONGODB_URI`, `MONGODB_DATABASE`, `MESSAGES_COLLECTION`, `API_HOST`, `API_PORT`, `MONGODB_PING_ON_STARTUP`, `UVICORN_RELOAD` (see [.env.example](.env.example)).
- **Docker**: [Dockerfile](Dockerfile) for the API image; [docker-compose.yml](docker-compose.yml) with `mongo` (always) and `microblog-api` (Compose **profile `full`**).
- **Make targets**: `docker-up`, `docker-down`, `docker-api`, `run-api` (MongoDB in Docker + API on host), `run-api-local`, `openapi-export`.
- **Tests**: Pydantic schema tests, repository tests, and FastAPI tests using [mongomock](https://github.com/mongomock/mongomock) (see [tests/conftest.py](tests/conftest.py)).
- **CLI**: `pdm run microblog-api` / console script `microblog-api` (Uvicorn with settings from `.env`).

### Changed

- Project dependencies and documentation updated to describe the microservice, Docker workflow, and API surface.

### Earlier

- Initial Python layout with PDM, Makefile (`build`, `test`, `run`, `clean`), CLI stub (`agentic-test`), and `.env` loading for the demo CLI.
