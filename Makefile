.PHONY: build test run clean docker-up docker-down docker-api run-api run-api-local openapi-export playwright-install playwright-test lint lint-fix typecheck mcp mpc playwright-py-install

# Install locked dependencies (dev) and build wheel/sdist
build:
	pdm sync --dev
	pdm build

# Python Playwright browsers (required for generated API tests and harness integration tests)
playwright-py-install:
	pdm run playwright install chromium

test:
	pdm run pytest tests --cov=agentic_test.ai_api_tester --cov-report=term-missing -q

lint:
	pdm run ruff check src/agentic_test/ai_api_tester tests/ai_api_tester
	pdm run ruff format --check src/agentic_test/ai_api_tester tests/ai_api_tester

lint-fix:
	pdm run ruff check --fix src/agentic_test/ai_api_tester tests/ai_api_tester
	pdm run ruff format src/agentic_test/ai_api_tester tests/ai_api_tester

typecheck:
	pdm run mypy src/agentic_test/ai_api_tester

# Start MCP stdio server (configure in Cursor / Claude Desktop via command below)
mcp:
	pdm run agentic-mcp-server

mpc: mcp

run:
	pdm run python -m agentic_test

clean:
	rm -rf dist build .pytest_cache .ruff_cache playwright/test-results playwright/playwright-report
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

# MongoDB only (for local API against localhost:27017)
docker-up:
	docker compose up -d mongo

docker-down:
	docker compose down

# API + MongoDB in Docker (profile "full")
docker-api:
	docker compose --profile full up --build -d

# Start MongoDB in Docker, then run the API on the host (see MONGODB_URI in `.env`)
run-api: docker-up
	pdm run microblog-api

# Run the API on the host only (MongoDB must already be reachable at MONGODB_URI)
run-api-local:
	pdm run microblog-api

openapi-export:
	pdm run python scripts/export_openapi.py

# Install Node deps and Playwright browsers (needed once per machine / CI image)
playwright-install:
	cd playwright && npm ci
	cd playwright && npx playwright install

# Run Playwright API tests (starts MongoDB + API on 127.0.0.1:18080 via webServer)
playwright-test: playwright-install
	cd playwright && npx playwright test
