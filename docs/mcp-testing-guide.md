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

Adjust the path and, if needed, how `pdm` is invoked (e.g. full path from `which pdm`).

```json
{
  "mcpServers": {
    "agentic-api-tester": {
      "command": "pdm",
      "args": ["run", "agentic-mcp-server"],
      "cwd": "/absolute/path/to/agentic-test"
    }
  }
}
```

If `pdm` is not on the PATH the GUI app uses, use a wrapper:

```json
{
  "mcpServers": {
    "agentic-api-tester": {
      "command": "/bin/bash",
      "args": ["-lc", "cd /absolute/path/to/agentic-test && pdm run agentic-mcp-server"],
      "cwd": "/absolute/path/to/agentic-test"
    }
  }
}
```

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
