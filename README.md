# agentic-test

A demo repository for MCP-oriented testing ideas, plus a **MongoDB-backed microblog REST API** built with **FastAPI**. The API is intended for local development or an all-in-Docker stack—suitable for standing up a small service and running automated tests against it.

See **[CHANGELOG.md](CHANGELOG.md)** for a history of what was added and when.

## AI API testing MCP harness (Python-only)

This repository includes an **MCP server** that exposes safe, typed tools so an LLM can introspect the microblog API, **generate Playwright Python tests** that use only **`APIRequestContext`** (no browser UI), save them under **`generated/tests/`**, run them with **pytest**, and inspect structured results. Implementation lives in [`src/agentic_test/ai_api_tester/`](src/agentic_test/ai_api_tester/).

**Full walkthrough:** [docs/mcp-testing-guide.md](docs/mcp-testing-guide.md) — setup, client configuration, designing scenarios, running tests via MCP, and troubleshooting.

**Layout:** `generated/tests/` (machine-writable), `generated/history/` (backups on update), `generated/artifacts/latest/` (JUnit + JSON report from the last run), `tests/handwritten_api/` (human-owned, read-only to `update_generated_test`), [`prompts/playwright_api_test_generation.md`](prompts/playwright_api_test_generation.md) (authoring checklist).

### For developers

- **Install:** `make build` and `make playwright-py-install` (Python Playwright browser binaries; Chromium is enough for API-only tests).
- **Quality gates:** `make lint` / `make lint-fix` (Ruff, scoped to the harness + its tests), `make typecheck` (mypy strict on `agentic_test.ai_api_tester`).
- **Tests:** `make test` runs the full pytest suite with **coverage** for `agentic_test.ai_api_tester`.
- **Run MCP (stdio):** `make mcp` (runs `pdm run agentic-mcp-server`). For **Claude Desktop**, prefer **`/path/to/repo/.venv/bin/agentic-mcp-server`** as the command—some clients do not pass `cwd`, and then `pdm run` fails with “pyproject.toml has not been initialized”. See [docs/mcp-testing-guide.md](docs/mcp-testing-guide.md). In a terminal, stop with **one** Ctrl+C and wait; repeated interrupts during shutdown can still print asyncio noise on some Python versions.
- **Adding a tool:** implement logic in [`handlers.py`](src/agentic_test/ai_api_tester/handlers.py), register in [`server.py`](src/agentic_test/ai_api_tester/server.py) with `@mcp.tool()`, return **JSON strings**, and add unit tests under [`tests/ai_api_tester/`](tests/ai_api_tester/). Never add generic shell execution.

### For testers / QA

- **Scenarios:** describe *Given / When / Then*, HTTP method, path, expected status, and important JSON keys. Follow [`prompts/playwright_api_test_generation.md`](prompts/playwright_api_test_generation.md).
- **Inspect workspace:** use MCP `list_tests` / `read_test_file`, or open `generated/tests/` and `.meta` JSON sidecars in the IDE.
- **Runs:** after `run_test` or `run_all_generated_tests`, use `get_test_artifacts` or open `generated/artifacts/latest/` for `junit.xml` and `pytest-report.json`.

### For AI agents and end users

**Capabilities**

- Discover service health and OpenAPI from a running base URL.
- List/read generated and handwritten API tests (writes only under `generated/`).
- Generate pytest modules using **sync `APIRequestContext`** and `API_BASE_URL` from the environment.
- Run one file or the whole generated suite (`pytest -k` filter supported).
- Start/stop **allow-listed** Docker Compose profiles (`mongo`, `full`) only—no arbitrary commands.

**MCP tools (JSON string results)**

| Tool | Role |
| ---- | ---- |
| `get_service_info` | Project metadata + `GET /health` probe. |
| `get_api_context` | Fetch `openapi.json` (or errors) from the target. |
| `list_tests` | Paths under `tests/handwritten_api/` and `generated/tests/`. |
| `read_test_file` | Contents + metadata if path is allow-listed. |
| `update_generated_test` | Patch a generated file; previous revision to `generated/history/`. |
| `delete_generated_test` | Remove generated test + sidecar metadata. |
| `generate_api_test_from_scenario` | Deterministic template + `.meta` JSON. |
| `run_test` | pytest on one file → artifacts + summary JSON. |
| `run_all_generated_tests` | pytest on `generated/tests/` with optional `-k` filter. |
| `get_test_artifacts` | Filenames in `generated/artifacts/latest/`. |
| `start_target_stack` | `profile`: `mongo` or `full` (Compose allow-list). |
| `stop_target_stack` | `docker compose down` for this repo’s compose file. |

**Example workflow (natural language → tools)**

1. `start_target_stack` with `mongo`, start the API locally (`make run-api-local`) or `start_target_stack` with `full`.
2. `get_service_info` / `get_api_context` using the correct `API_BASE_URL`.
3. `generate_api_test_from_scenario` for e.g. `GET /messages` with expected `200` and keys `items`, `total`.
4. `run_test` on the returned relative path with the same `api_base_url`.
5. `get_test_artifacts` to collect reports; iterate with `update_generated_test` if needed.

> **Note:** The separate **Node + Playwright** package under [`playwright/`](playwright/) is optional and legacy for this repo; the MCP harness and generated tests are **Python + Playwright** only.

## Prerequisites

- **Python** 3.11 or newer ([python.org](https://www.python.org/downloads/) or your OS package manager)
- **[PDM](https://pdm-project.org/latest/)** — package and environment manager
- **GNU Make** — macOS and Linux usually include it; on Windows, use WSL, Git Bash, or another environment that provides `make`
- **Docker** and **Docker Compose** — for MongoDB and/or the full API stack ([Docker Desktop](https://docs.docker.com/desktop/) or equivalent)
- **Node.js** 18+ and **npm** — optional, only for the legacy [Playwright](https://playwright.dev/) **TypeScript** tests under [`playwright/`](playwright/) (not required for the Python MCP harness)

Install PDM (pick one):

- [Official installer](https://pdm-project.org/latest/#installation)
- Homebrew: `brew install pdm`

## Developer onboarding

1. **Install PDM** (see [Prerequisites](#prerequisites)) if needed.

2. **Install dependencies and build artifacts**:

   ```bash
   make build
   ```

3. **Configure environment variables** — copy the template and edit for your machine:

   ```bash
   cp .env.example .env
   ```

   Variables are documented in [.env.example](.env.example). The API uses [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) to read `.env` from the project root (next to `pyproject.toml`). Values already set in the process environment are not overwritten by `.env`.

4. **Run Python tests**:

   ```bash
   make test
   ```

5. **Install Python Playwright browsers** (for generated API tests and the MCP harness):

   ```bash
   make playwright-py-install
   ```

6. **Install Playwright and run HTTP API tests** (optional **Node** path; needs Docker for MongoDB):

   ```bash
   make playwright-test
   ```

   See [Playwright API testing](#playwright-api-testing).

7. **Run the demo CLI** (optional):

   ```bash
   make run
   ```

Repeat **`make build`** after pulls when `pdm.lock` changes.

## Microblog service

### Capabilities

- Persist **microblog messages** in MongoDB. Each document includes:
  - **`id`**: MongoDB `ObjectId` as a string (assigned on create)
  - **`author_first_name`**, **`author_last_name`**, **`author_email`**
  - **`text`**: body, maximum **255** characters
  - **`created_at`**, **`updated_at`**: UTC timestamps (set on create; `updated_at` changes on successful patch)
- Expose a **REST API** with JSON request and response bodies.
- Provide **interactive API documentation** (Swagger UI) at the **site root** [`/`](http://127.0.0.1:8000/), with **OpenAPI JSON** at [`/openapi.json`](http://127.0.0.1:8000/openapi.json) and **ReDoc** at [`/redoc`](http://127.0.0.1:8000/redoc).

Committed static copies of the spec live under **[docs/openapi.yaml](docs/openapi.yaml)** and **[docs/openapi.json](docs/openapi.json)**. Regenerate them after changing routes or models:

```bash
make openapi-export
```

### REST interface

| Method | Path | Description |
| ------ | ---- | ----------- |
| `POST` | `/messages` | Create a message. **201** + body on success. |
| `GET` | `/messages/{id}` | Get one message by `id`. **404** if missing or invalid id. |
| `GET` | `/messages` | List messages. Query: `skip` (default `0`), `limit` (default `20`, max `100`), `sort_by` (`created_at` or `updated_at`), `sort_order` (`asc` or `desc`). Response includes `items`, `total`, `skip`, `limit`. |
| `PATCH` | `/messages/{id}` | Partial update; only sent fields change. **404** if not found. |
| `DELETE` | `/messages/{id}` | Delete. **204** on success; **404** if not found. |
| `GET` | `/health` | `{"status":"ok"}` when the process is up (does not deep-check MongoDB). |

**Create / replace body shape** (JSON keys):

```json
{
  "author_first_name": "string",
  "author_last_name": "string",
  "author_email": "valid-email@example.com",
  "text": "up to 255 characters"
}
```

**Patch** accepts any subset of those fields (all optional).

### Running locally (API on host, MongoDB in Docker)

Start MongoDB, then run Uvicorn using PDM (uses `API_HOST`, `API_PORT`, `MONGODB_URI` from `.env`):

```bash
make run-api
```

`make run-api` runs `docker compose up -d mongo` first, then `pdm run microblog-api`. For **auto-reload** during development:

```bash
UVICORN_RELOAD=true pdm run microblog-api
```

If MongoDB is already running elsewhere, skip Compose and use:

```bash
make run-api-local
```

### Running fully in Docker (API + MongoDB)

Build and start both services (Compose **profile `full`**):

```bash
make docker-api
```

- API: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) (Swagger UI)
- MongoDB is **not** published to the host in this profile (only the `mongo` service on the Compose network). To use tools on your host against that database, add a `ports` mapping to `mongo` or use `docker compose exec`.

Stop the stack (including volumes if you add `-v` yourself):

```bash
make docker-down
```

`make docker-up` starts **only** MongoDB with port **27017** mapped to localhost—useful with `make run-api-local` and `MONGODB_URI=mongodb://127.0.0.1:27017`.

### Implementation notes

- **Package layout**: `agentic_test.microblog` (schemas, repository), `agentic_test.api` (FastAPI app and routes), `agentic_test.config` (settings).
- **Mongo client**: one client per process, opened in the app **lifespan** and stored on `app.state`.
- **Startup**: unless `MONGODB_PING_ON_STARTUP=false`, the API pings MongoDB before serving; connection string and timeouts come from code and `MONGODB_URI`.

## Using Make

| Target | Purpose |
| ------ | ------- |
| `make build` | `pdm sync --dev` and `pdm build` (wheel/sdist under `dist/`). |
| `make test` | `pytest` for `tests/` with **coverage** on `agentic_test.ai_api_tester`. |
| `make run` | Demo CLI: `python -m agentic_test`. |
| `make clean` | Remove `dist/`, `build/`, pytest/ruff caches, `__pycache__`. |
| `make docker-up` | Start **MongoDB** via Compose (`mongo` service). |
| `make docker-down` | `docker compose down`. |
| `make docker-api` | Build and run **API + MongoDB** (`--profile full`). |
| `make run-api` | `docker-up` then run the API on the host with `microblog-api`. |
| `make run-api-local` | Run the API on the host only (MongoDB must be reachable). |
| `make openapi-export` | Write `docs/openapi.json` and `docs/openapi.yaml` from the FastAPI app. |
| `make playwright-py-install` | `pdm run playwright install chromium` (Python Playwright). |
| `make lint` / `make lint-fix` | Ruff on `ai_api_tester` + `tests/ai_api_tester`. |
| `make typecheck` | mypy (strict) on `src/agentic_test/ai_api_tester`. |
| `make mcp` | Start the MCP stdio server (`agentic-mcp-server`). |
| `make playwright-install` | `npm ci` and `npx playwright install` in [`playwright/`](playwright/). |
| `make playwright-test` | Install Playwright deps, then run `npx playwright test` (starts MongoDB + API on **127.0.0.1:18080** unless skipped; see below). |

PDM equivalents: `pdm sync --dev`, `pdm run pytest`, `pdm run microblog-api`, `pdm run agentic-test`.

## Project structure

```text
agentic-test/
├── CHANGELOG.md
├── Dockerfile
├── Makefile
├── README.md
├── docker-compose.yml
├── docs/
│   ├── mcp-testing-guide.md  # MCP setup, design, run tests
│   ├── openapi.json       # generated; run make openapi-export
│   └── openapi.yaml
├── pyproject.toml
├── pdm.lock
├── generated/             # MCP harness workspace (tests, history, artifacts)
├── prompts/
│   └── playwright_api_test_generation.md
├── scripts/
│   ├── export_openapi.py
│   └── run-api-for-playwright.sh   # MongoDB + Uvicorn for Playwright webServer
├── playwright/
│   ├── package.json
│   ├── package-lock.json
│   ├── playwright.config.ts
│   └── tests/api/messages.spec.ts
├── .env.example
├── src/agentic_test/
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py              # CLI entry (dotenv + demo print)
│   ├── config.py            # shared settings (API + future use)
│   ├── ai_api_tester/       # MCP server + harness (Playwright API tests)
│   │   ├── server.py
│   │   ├── handlers.py
│   │   └── ...
│   ├── api/
│   │   ├── app.py           # FastAPI app, lifespan, Swagger at /
│   │   ├── cli.py           # Uvicorn entry for microblog-api script
│   │   └── routes/messages.py
│   └── microblog/
│       ├── schemas.py
│       ├── repository.py
│       └── deps.py
└── tests/
    ├── conftest.py          # mongomock patch + DB cleanup between API tests
    ├── test_api.py
    ├── test_main.py
    ├── test_repository.py
    └── test_schemas.py
```

PDM keeps a virtualenv under **`.venv`** (gitignored). Do not commit **`.env`**.

## Configuration

- **CLI** (`make run`): `APP_ENV`, `DEBUG` (see [.env.example](.env.example)).
- **Microblog API**: `MONGODB_URI`, `MONGODB_DATABASE`, `MESSAGES_COLLECTION`, `API_HOST`, `API_PORT`, `MONGODB_PING_ON_STARTUP`, `UVICORN_RELOAD`.
- **Playwright** (optional): `PLAYWRIGHT_SKIP_WEBSERVER`, `API_BASE_URL`, `PLAYWRIGHT_API_PORT` (see [Playwright API testing](#playwright-api-testing)).
- In CI, set the same variables in the job environment instead of committing `.env`.

## Tests

### Python (`pytest`)

- **Unit / API tests** use [mongomock](https://github.com/mongomock/mongomock) so the suite does not require a live MongoDB (`tests/conftest.py` patches `pymongo.MongoClient` and sets `MONGODB_PING_ON_STARTUP=false` for pytest).

### Playwright API testing

End-to-end HTTP checks run against a **real** MongoDB and FastAPI process. The Playwright config ([`playwright/playwright.config.ts`](playwright/playwright.config.ts)) uses [`webServer`](https://playwright.dev/docs/test-webserver) to run [`scripts/run-api-for-playwright.sh`](scripts/run-api-for-playwright.sh): it starts the Compose **`mongo`** service, waits until it answers `ping`, then runs **Uvicorn** on **`127.0.0.1:18080`** so the suite does not fight with a dev server on port **8000**.

**Commands**

```bash
make playwright-install   # once per machine / CI image
make playwright-test      # install + run all Playwright tests
```

Or manually:

```bash
cd playwright && npm ci && npx playwright install && npx playwright test
```

**Environment variables**

| Variable | Purpose |
| -------- | ------- |
| `PLAYWRIGHT_SKIP_WEBSERVER` | If set (any value), Playwright does **not** start Mongo/API; you must run the stack yourself and point `API_BASE_URL` at it. |
| `API_BASE_URL` | Base URL for requests (default `http://127.0.0.1:18080` when `PLAYWRIGHT_API_PORT` is default). |
| `PLAYWRIGHT_API_PORT` | Port passed to the startup script and used in the default `API_BASE_URL` (default **`18080`**). |
| `CI` | Many CI systems set `CI=1`. The config treats only `1`, `true`, or `yes` (case-insensitive) as CI so that a shell default like `CI=false` does not break `webServer.reuseExistingServer`. In CI, Playwright **always** starts its own server on the chosen port (no reuse). |

**What is covered**

The spec [`playwright/tests/api/messages.spec.ts`](playwright/tests/api/messages.spec.ts) exercises `GET /health`, Swagger at `/`, `GET /openapi.json`, full CRUD on `/messages`, list query parameters, validation **422**, and **404** cases. Tests in the file run **serially** against one shared database.

**Requirements**

- **Docker** available to the user running tests (for MongoDB).
- **`pdm`** on `PATH` (the startup script runs `pdm run uvicorn …`).
- **Node/npm** as above.

### Manual checks

- For ad hoc exploration against **real** MongoDB, start the database (for example `make docker-up`), run the API, and drive it with HTTP clients; the **OpenAPI** spec documents the contract.
