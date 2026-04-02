# agentic-test

A demo repository for MCP-oriented testing ideas, plus a **MongoDB-backed microblog REST API** built with **FastAPI**. The API is intended for local development or an all-in-Docker stack—suitable for standing up a small service and running automated tests against it.

See **[CHANGELOG.md](CHANGELOG.md)** for a history of what was added and when.

## Prerequisites

- **Python** 3.11 or newer ([python.org](https://www.python.org/downloads/) or your OS package manager)
- **[PDM](https://pdm-project.org/latest/)** — package and environment manager
- **GNU Make** — macOS and Linux usually include it; on Windows, use WSL, Git Bash, or another environment that provides `make`
- **Docker** and **Docker Compose** — for MongoDB and/or the full API stack ([Docker Desktop](https://docs.docker.com/desktop/) or equivalent)

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

4. **Run tests**:

   ```bash
   make test
   ```

5. **Run the demo CLI** (optional):

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
| `make test` | `pytest` (includes API tests with **mongomock**; no Docker required). |
| `make run` | Demo CLI: `python -m agentic_test`. |
| `make clean` | Remove `dist/`, `build/`, pytest/ruff caches, `__pycache__`. |
| `make docker-up` | Start **MongoDB** via Compose (`mongo` service). |
| `make docker-down` | `docker compose down`. |
| `make docker-api` | Build and run **API + MongoDB** (`--profile full`). |
| `make run-api` | `docker-up` then run the API on the host with `microblog-api`. |
| `make run-api-local` | Run the API on the host only (MongoDB must be reachable). |
| `make openapi-export` | Write `docs/openapi.json` and `docs/openapi.yaml` from the FastAPI app. |

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
│   ├── openapi.json       # generated; run make openapi-export
│   └── openapi.yaml
├── pyproject.toml
├── pdm.lock
├── scripts/
│   └── export_openapi.py
├── .env.example
├── src/agentic_test/
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py              # CLI entry (dotenv + demo print)
│   ├── config.py            # shared settings (API + future use)
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
- In CI, set the same variables in the job environment instead of committing `.env`.

## Tests

- **Unit / API tests** use [mongomock](https://github.com/mongomock/mongomock) so the suite does not require a live MongoDB (`tests/conftest.py` patches `pymongo.MongoClient` and sets `MONGODB_PING_ON_STARTUP=false` for pytest).
- For manual or pipeline checks against **real** MongoDB, start the database (for example `make docker-up`), run the API, and drive it with HTTP clients or contract tests of your choice; the **OpenAPI** spec documents the contract.
