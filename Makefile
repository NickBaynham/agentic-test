.PHONY: build test run clean

# Install locked dependencies (dev) and build wheel/sdist
build:
	pdm sync --dev
	pdm build

test:
	pdm run pytest

run:
	pdm run python -m agentic_test

clean:
	rm -rf dist build .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
