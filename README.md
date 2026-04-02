# agentic-test

A MCP enabled testing framework that demonstrates agentic testing.

## Prerequisites

- **Python** 3.11 or newer ([python.org](https://www.python.org/downloads/) or your OS package manager)
- **[PDM](https://pdm-project.org/latest/)** — the project’s package and environment manager
- **GNU Make** — macOS and Linux usually include it; on Windows, use WSL, Git Bash, or another environment that provides `make`

Install PDM (pick one):

- [Official installer](https://pdm-project.org/latest/#installation)
- Homebrew: `brew install pdm`

## Developer onboarding

Follow these steps when you first clone the repository.

1. **Install PDM** (see [Prerequisites](#prerequisites)) if you do not already have it.

2. **Install dependencies and build artifacts** — from the repository root:

   ```bash
   make build
   ```

   This runs `pdm sync --dev` (creates or updates the project virtualenv from `pdm.lock` and installs the package in editable mode) and `pdm build` (produces a source distribution and wheel under `dist/`). After this, you can run tests and the app without manually invoking `pdm install`.

3. **Configure local environment variables** — the app reads a `.env` file at the project root (the directory that contains `pyproject.toml`). It is not committed to git.

   ```bash
   cp .env.example .env
   ```

   Edit `.env` for your machine. Values are documented in [.env.example](.env.example). The application loads `.env` on startup via [python-dotenv](https://pypi.org/project/python-dotenv/) without overriding variables that are already set in your shell or CI.

4. **Verify the setup**:

   ```bash
   make test
   make run
   ```

You can repeat **`make build`** after pulling changes whenever `pdm.lock` is updated, so your environment stays aligned with the team lockfile.

## Using Make

All targets are meant to be run from the **repository root** (where the `Makefile` lives).

| Target   | What it does |
| -------- | ------------ |
| `make build` | Syncs locked dependencies (including dev tools), installs the project into the PDM-managed environment, and builds wheel/sdist under `dist/`. |
| `make test`  | Runs the test suite with pytest (`pdm run pytest`). |
| `make run`   | Runs the application module (`pdm run python -m agentic_test`). |
| `make clean` | Removes `dist/`, `build/`, pytest and ruff caches, and `__pycache__` directories. Does not remove the virtualenv or `.env`. |

Equivalent PDM-only commands (if you prefer not to use Make):

- `pdm sync --dev` then `pdm build` — same as `make build` (without `make clean` first)
- `pdm run pytest` — same as `make test`
- `pdm run python -m agentic_test` or `pdm run agentic-test` — same entrypoint as `make run`

## Project structure

```text
agentic-test/
├── Makefile              # build, test, run, clean
├── pyproject.toml        # project metadata, dependencies, pytest config
├── pdm.lock              # locked dependency versions (commit this)
├── .env.example          # documented template for local `.env`
├── .env                  # local secrets and overrides (create yourself; gitignored)
├── src/
│   └── agentic_test/     # installable Python package
│       ├── __init__.py
│       ├── __main__.py   # enables `python -m agentic_test`
│       └── main.py       # loads `.env`, application entry logic
├── tests/                # pytest tests
│   └── test_main.py
├── dist/                 # build output from `pdm build` / `make build` (gitignored)
└── README.md
```

PDM keeps a project virtualenv under **`.venv`** by default (gitignored). Do not commit `.env` or `.venv`.

## Configuration

- Copy **`.env.example`** to **`.env`** and adjust variables for local development.
- The app resolves the project root by finding `pyproject.toml`, then loads **`.env`** from that directory.
- For CI or servers, set environment variables in the host or orchestrator instead of relying on a `.env` file; the same variable names apply.
