# Changelog

All notable changes to this project are documented in this file. The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] — 2026-04-02

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
