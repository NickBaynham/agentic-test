# MCP testing guide: setup, design, and run API tests

This guide explains how to wire the **agentic-api-tester** MCP server into a client, then use MCP tools to **discover** the API, **design** Playwright-based API tests, and **run** them against your service.

For a short overview and tool table, see the [README](../README.md#ai-api-testing-mcp-harness-python-only). For authoring rules used when generating tests, see [prompts/playwright_api_test_generation.md](../prompts/playwright_api_test_generation.md).

---

## 1. What you are connecting

- **Transport:** stdio (the server speaks MCP over standard input/output).
- **Process:** `pdm run agentic-mcp-server` (or `make mcp`), with **current working directory = repository root** (the directory that contains `pyproject.toml`).
- **Workspace:** The server resolves paths relative to that repo. Writes are allowed only under `generated/` (see [Safety](#7-safety-and-limitations)).

All tools return **JSON as a string** (parse the tool result in your client or ask the model to interpret it).

---

## 2. Prerequisites

| Requirement | Why |
| ----------- | --- |
| Python 3.11+ | Project constraint |
| [PDM](https://pdm-project.org/latest/) | Installs deps and runs the server |
| This repo cloned locally | MCP `cwd` must point here |
| Docker / Docker Compose | Optional but typical for MongoDB + API (`start_target_stack`) |
| `make playwright-py-install` once | Python Playwright needs Chromium (or full install) for `APIRequestContext` in pytest |

You do **not** need Node.js for this flow unless you also use the legacy TypeScript Playwright package under `playwright/`.

---

## 3. One-time setup

From the repository root:

```bash
make build
make playwright-py-install
```

Optional: copy [`.env.example`](../.env.example) to `.env` if you run the FastAPI app with `make run-api` / `microblog-api` outside MCP.

Verify the server starts (it will wait on stdio; press Ctrl+C to exit):

```bash
make mcp
# or: pdm run agentic-mcp-server
```

---

## 4. Connecting your MCP client

Point the client at **PDM** (or the project venv’s Python) so `PYTHONPATH` and dependencies resolve correctly. The critical settings are:

- **Command:** must run the installed console script in this project’s environment.
- **`cwd`:** absolute path to the repo root.

### 4.1 Example: Cursor / VS Code–style `mcp.json`

**Recommended (Claude Desktop / apps that ignore `cwd`):** call the project **venv** script so PDM is not required at launch and the project root is discovered from the installed package:

```json
{
  "mcpServers": {
    "agentic-api-tester": {
      "command": "/absolute/path/to/agentic-test/.venv/bin/agentic-mcp-server",
      "args": [],
      "cwd": "/absolute/path/to/agentic-test"
    }
  }
}
```

Equivalent with Python:

```json
{
  "mcpServers": {
    "agentic-api-tester": {
      "command": "/absolute/path/to/agentic-test/.venv/bin/python",
      "args": ["-m", "agentic_test.ai_api_tester.server"],
      "cwd": "/absolute/path/to/agentic-test"
    }
  }
}
```

**Alternative:** `pdm run agentic-mcp-server` only if the client **honors** `cwd` (repo root). If you see `The pyproject.toml has not been initialized yet`, PDM is running in the wrong directory—switch to the venv command above or use:

```json
{
  "mcpServers": {
    "agentic-api-tester": {
      "command": "/bin/bash",
      "args": ["-lc", "cd /absolute/path/to/agentic-test && exec pdm run agentic-mcp-server"]
    }
  }
}
```

If `pdm` is not on the PATH the GUI app uses, use the full path to `pdm` inside the `-lc` string.

### 4.2 Claude Desktop (illustrative)

Claude Desktop uses an MCP config file on your OS; add a server entry with the same idea: **stdio command + repo `cwd`**. Refer to [Anthropic’s MCP documentation](https://modelcontextprotocol.io/) for the exact file location and schema for your version.

### 4.3 After connecting

- Enable the **agentic-api-tester** server in the client.
- In chat, you should see tools such as `get_service_info`, `get_api_context`, `generate_api_test_from_scenario`, `run_test`, etc.

---

## 5. Bringing the API online (optional but typical)

The microblog API needs MongoDB. Two patterns:

| Approach | MCP / shell |
| -------- | ----------- |
| **Mongo in Docker, API on host** | `start_target_stack` with `profile: "mongo"`, then start the API (e.g. `make run-api-local` in a terminal with `.env` set). |
| **Mongo + API in Docker** | `start_target_stack` with `profile: "full"` (Compose profile `full`). |

Use **`stop_target_stack`** when you want `docker compose down` for this repo’s `docker-compose.yml` only (no arbitrary compose files).

**Important:** `get_service_info` and `get_api_context` need a reachable **base URL** (see below). Default in settings is `http://127.0.0.1:8000`; if your API listens elsewhere, pass `api_base_url` on each tool call that supports it.

---

## 6. Designing tests through MCP

Design is an iterative loop: **discover contract → choose scenarios → generate or edit → run → refine**.

### 6.1 Discover the service

1. **`get_service_info`**  
   - Optional argument: `api_base_url` (e.g. `http://127.0.0.1:8000`).  
   - Use the JSON to confirm the **health** probe (`/health` by default) and project metadata.

2. **`get_api_context`**  
   - Same optional `api_base_url`.  
   - Parses **`/openapi.json`** from the running service. Use the returned spec to choose paths, methods, status codes, and JSON shapes.

### 6.2 Inspect existing tests

- **`list_tests`** — paths under `generated/tests/` and `tests/handwritten_api/`.
- **`read_test_file`** — `relative_path` from repo root, e.g. `generated/tests/test_generated_probe_health.py`. Only those trees are readable.

### 6.3 Authoring scenarios for generation

Generated tests are **pytest** modules that use **only** Playwright’s sync **`APIRequestContext`** (via `sync_playwright().request.new_context(base_url=...)`). They read **`API_BASE_URL`** from the environment when pytest runs.

When calling **`generate_api_test_from_scenario`**, supply:

| Argument | Purpose |
| -------- | ------- |
| `scenario` | Short natural-language description (stored in docstring). |
| `endpoint` | Path such as `/health` or `/messages`. |
| `http_method` | One of `GET`, `POST`, `PATCH`, `DELETE`, `PUT`. |
| `expected_status` | Integer HTTP status (e.g. `200`, `201`). |
| `response_json_keys` | Optional list of keys that must exist in the JSON body (e.g. `["status"]`, `["items","total"]`). |
| `json_body` | Optional dict for `POST`/`PATCH`/`PUT` JSON body. |

The tool writes:

- `generated/tests/test_generated_<slug>.py`
- `generated/tests/.meta/<stem>.json` (metadata)

It does **not** overwrite handwritten tests under `tests/handwritten_api/`.

### 6.4 Refining tests

- **`update_generated_test`** — new full file `content` for a path under `generated/tests/`; previous file is copied to `generated/history/`.
- **`delete_generated_test`** — removes a generated test and its `.meta` sidecar.
- Handwritten files **cannot** be updated or deleted by these tools (by design).

For human-readable authoring rules, keep [prompts/playwright_api_test_generation.md](../prompts/playwright_api_test_generation.md) open while designing prompts.

---

## 7. Running tests through MCP

### 7.1 Single file: `run_test`

Arguments:

- **`relative_path`** — e.g. `generated/tests/test_generated_probe_health.py`.
- **`api_base_url`** (optional) — forwarded into the pytest subprocess as **`API_BASE_URL`**. The generated code uses `os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")`, so passing this argument is how you aim tests at the right host without editing files.

The harness runs **pytest** (subprocess) with JUnit XML and **pytest-json-report** under **`generated/artifacts/latest/`**.

The tool result JSON includes:

- `passed` (boolean rollup)
- `exit_code`
- `stdout_tail` / `stderr_tail`
- `junit` (parsed summary)
- `json_report` (raw plugin output when present)
- `artifacts` — repo-relative paths to `junit.xml` and `pytest-report.json`

### 7.2 Whole generated suite: `run_all_generated_tests`

Arguments:

- **`api_base_url`** (optional) — same as above.
- **`tag_filter`** (optional) — passed to pytest **`-k`** (e.g. a substring or `generated_api` if you use that marker).

Use this for regression after adding multiple files under `generated/tests/`.

### 7.3 Listing artifact files: `get_test_artifacts`

Returns the **`generated/artifacts/latest/`** directory (repo-relative) and **file names** present after the latest run. Open those files in the IDE for full XML/JSON.

---

## 8. End-to-end workflow (checklist)

Use this as a conversation template with an MCP-enabled agent:

1. **Connect** the client using [section 4](#4-connecting-your-mcp-client).
2. **`start_target_stack`** with `mongo` or `full`; ensure the API is reachable at your chosen base URL.
3. **`get_service_info`** with that `api_base_url`.
4. **`get_api_context`** with the same base URL; inspect `paths` and schemas.
5. **`generate_api_test_from_scenario`** for one endpoint (start with `GET /health`).
6. **`run_test`** with the returned `relative_path` and the same `api_base_url`.
7. If red: read `stderr_tail` / `junit` in the JSON; **`read_test_file`**, then **`update_generated_test`** or regenerate.
8. **`run_all_generated_tests`** when the suite grows.
9. **`get_test_artifacts`** to confirm report files on disk.
10. **`stop_target_stack`** when finished (optional).

For **ready-made chat prompts** (per endpoint, coverage, and test data), see [section 12](#12-example-prompts-copy-paste).

---

## 9. Safety and limitations

- **No arbitrary shell:** tools do not expose a general command runner.
- **Sandboxed writes:** only `generated/` (with traversal checks). Handwritten tests are read-only for update/delete tools.
- **Docker:** only the repo’s **`docker-compose.yml`** with profiles **`mongo`** and **`full`** as implemented in code.
- **Secrets:** do not put tokens into scenario text if logs might be retained; prefer env-based configuration for the API itself.

---

## 10. Troubleshooting

| Symptom | Things to check |
| ------- | ---------------- |
| Noisy tracebacks or fatal errors when stopping `make mcp` with Ctrl+C | Use **one** Ctrl+C and wait a second for the stdio server to exit. A **second** interrupt during asyncio/anyio teardown can still trigger long tracebacks or stdin-lock shutdown bugs on some Python versions; that is harmless if the process exits. The server treats the first interrupt as a normal stop. |
| MCP server fails to start | `cwd` is repo root; `pdm run agentic-mcp-server` works in a terminal from that directory. |
| `get_service_info` / `get_api_context` errors | API is up; URL includes scheme/port; firewall; correct `api_base_url` argument. |
| `run_test` fails with Playwright errors | Run `make playwright-py-install` on this machine. |
| Tests hit wrong host | Pass **`api_base_url`** on `run_test` / `run_all_generated_tests` so `API_BASE_URL` is set for pytest. |
| Permission / path errors | Path must be under `generated/tests/` or `tests/handwritten_api/` for read; writes only `generated/tests/`. |

---

## 11. Related commands (without MCP)

For local debugging without an LLM:

```bash
make test          # full pytest + coverage on ai_api_tester
make lint
make typecheck
```

These complement MCP-driven workflows but do not replace them.

---

## 12. Example prompts (copy-paste)

Use these with an MCP-enabled assistant that has **agentic-api-tester** enabled. Adjust the base URL if yours is not `http://127.0.0.1:8000`. The model should call the **named MCP tools** (not guess HTTP from thin air) unless you are only asking for planning.

The Microblog API (from OpenAPI) exposes:

| Method | Path | Typical success status |
| ------ | ---- | ------------------------ |
| `GET` | `/health` | `200` |
| `GET` | `/messages` | `200` (query: `skip`, `limit`, `sort_by`, `sort_order`) |
| `POST` | `/messages` | `201` |
| `GET` | `/messages/{message_id}` | `200` |
| `PATCH` | `/messages/{message_id}` | `200` |
| `DELETE` | `/messages/{message_id}` | `204` |

`generate_api_test_from_scenario` emits a **literal** path string. For routes with `{message_id}`, either substitute a real id (see [Workflow: reusing a message id](#workflow-reusing-a-message-id)) or ask the assistant to **`update_generated_test`** after you know the id.

### Bootstrap and discovery

**Bring the stack up and load the contract**

> Use MCP `start_target_stack` with profile `mongo` or `full` as appropriate. When the API is up, call `get_service_info` with `api_base_url` `http://127.0.0.1:8000`, then `get_api_context` with the same URL. Summarize which paths exist and what each method expects for request bodies and success status codes.

**Quick health check only**

> Call `get_service_info` with `api_base_url` `http://127.0.0.1:8000` and report whether the health check succeeded and what JSON you saw.

### Good coverage (one conversation)

**Generate a small suite covering every route**

> OpenAPI for this service lists `GET /health`, `GET /messages`, `POST /messages`, `GET /messages/{message_id}`, `PATCH /messages/{message_id}`, and `DELETE /messages/{message_id}`. Using MCP only: (1) `get_api_context` at `http://127.0.0.1:8000`. (2) Generate one pytest file per successful path/method using `generate_api_test_from_scenario`: health 200 with key `status`; list messages 200 with keys `items`, `total`, `skip`, `limit`; create message 201 with keys `id`, `text`, `author_email` and a realistic `json_body` (see below). (3) For GET/PATCH/DELETE by id, follow a two-step flow: first ensure there is a create test, tell me the id to embed, or generate placeholder paths and explain I must replace `MESSAGE_ID`. (4) Add one extra test: `GET /messages?skip=0&limit=5&sort_by=created_at&sort_order=asc` expecting 200 and the same list keys. (5) Run `run_all_generated_tests` with `api_base_url` `http://127.0.0.1:8000` and fix any failures using `read_test_file` / `update_generated_test`.

**Regression after changes**

> Run `list_tests`, then `run_all_generated_tests` with `api_base_url` `http://127.0.0.1:8000`. If anything fails, show `stderr_tail` from the tool result and open `get_test_artifacts` paths for full JUnit.

### Per-endpoint generation prompts

**`GET /health`**

> Call `generate_api_test_from_scenario` with scenario `Health endpoint returns JSON status`, endpoint `/health`, `http_method` `GET`, `expected_status` `200`, `response_json_keys` `["status"]`.

**`GET /messages` (default pagination)**

> Call `generate_api_test_from_scenario` with scenario `List messages returns paginated JSON`, endpoint `/messages`, `http_method` `GET`, `expected_status` `200`, `response_json_keys` `["items", "total", "skip", "limit"]`.

**`GET /messages` (query parameters)**

> Call `generate_api_test_from_scenario` with scenario `List messages with explicit sort and page size`, endpoint `/messages?skip=0&limit=10&sort_by=updated_at&sort_order=asc`, `http_method` `GET`, `expected_status` `200`, `response_json_keys` `["items", "total", "skip", "limit"]`.

**`POST /messages` (fixed example body)**

> Call `generate_api_test_from_scenario` with scenario `Create message with sample author and body`, endpoint `/messages`, `http_method` `POST`, `expected_status` `201`, `response_json_keys` `["id", "author_email", "text", "created_at"]`, and `json_body` exactly:
> `{"author_first_name": "Ada", "author_last_name": "Lovelace", "author_email": "ada.lovelace@example.com", "text": "First automated post"}`.

**`GET /messages/{message_id}`**

> After we have a real message id (from a passing `POST /messages` test or from the database), call `generate_api_test_from_scenario` with scenario `Fetch single message by id`, endpoint `/messages/<paste-id-here>`, `http_method` `GET`, `expected_status` `200`, `response_json_keys` `["id", "text", "author_first_name", "author_last_name", "author_email", "created_at", "updated_at"]`.

**`PATCH /messages/{message_id}`**

> Call `generate_api_test_from_scenario` with scenario `Update message text only`, endpoint `/messages/<paste-id-here>`, `http_method` `PATCH`, `expected_status` `200`, `response_json_keys` `["id", "text", "updated_at"]`, and `json_body` `{"text": "Updated via MCP harness"}`.

**`DELETE /messages/{message_id}`**

> Call `generate_api_test_from_scenario` with scenario `Delete message returns no content`, endpoint `/messages/<paste-id-here>`, `http_method` `DELETE`, `expected_status` `204`. Do not pass `response_json_keys` (empty body).

### Generating and using test data

**Ask the model to invent data (then pass it into the tool)**

> Invent a realistic `MessageCreate` payload: unique `author_email` (use a fake `@example.com` domain), valid names (1–120 chars), and `text` between 1 and 255 characters. Then call `generate_api_test_from_scenario` for `POST /messages` with `expected_status` `201` and `response_json_keys` `["id", "author_email", "text"]`, using your invented object as `json_body`. Finally run `run_test` on the new file with `api_base_url` `http://127.0.0.1:8000` and tell me the created `id` from the pytest output if the assertion prints the body.

**Varied payloads for stronger coverage**

> Generate three separate `POST /messages` tests with different `json_body` values (different authors and text) but the same expected keys `["id", "text"]`. Use `list_tests` to avoid duplicate filenames if the slug collides; if needed, shorten or vary the scenario string slightly. Run `run_all_generated_tests` when done.

**PATCH with partial updates**

> Using the OpenAPI `MessageUpdate` schema (all fields optional), generate a `PATCH` test with `json_body` containing only `{"text": "Partial patch"}` and optionally a second test that patches `author_email` only. Use the same `message_id` in the endpoint path for both.

### Workflow: reusing a message id

1. Generate and **run** `POST /messages` until green; note the `id` in the response (expand the assertion temporarily with `update_generated_test` to log `response.text()` if needed, or read Playwright failure output).
2. Call `generate_api_test_from_scenario` for `GET`, `PATCH`, and `DELETE` with `/messages/<that-id>`.
3. Run **`DELETE` last** if you want the other tests to remain valid in one session, or use a fresh id per run.

Alternatively, **`read_test_file`** on the POST test and **`update_generated_test`** to hard-code an id you copied from a manual `curl` or Swagger UI call.

### Running what you generated

**Single file**

> Run MCP `run_test` with `relative_path` set to the path returned from `generate_api_test_from_scenario` (under `generated/tests/`) and `api_base_url` `http://127.0.0.1:8000`.

**Whole generated directory**

> Run `run_all_generated_tests` with `api_base_url` `http://127.0.0.1:8000`, then `get_test_artifacts` and list the paths to `junit.xml` and `pytest-report.json`.

### Negative / edge cases (optional)

**Validation error**

> Call `generate_api_test_from_scenario` for `POST /messages` with `json_body` `{"author_first_name": "", "author_last_name": "X", "author_email": "not-an-email", "text": "bad"}`, `expected_status` `422`, and no `response_json_keys` (or keys you know FastAPI returns on validation errors, if you want strict asserts).

**Not found**

> This API returns **404** for unknown or invalid MongoDB ids. Generate `GET /messages/507f1f77bcf86cd799439011` with `expected_status` `404` if that id is not in your database (or pick another valid 24-hex ObjectId string you know is absent).
