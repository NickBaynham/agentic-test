.PHONY: build test run clean docker-up docker-down docker-api run-api run-api-local openapi-export playwright-install playwright-test

# Install locked dependencies (dev) and build wheel/sdist
build:
	pdm sync --dev
	pdm build

test:
	pdm run pytest

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
