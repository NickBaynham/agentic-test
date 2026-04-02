#!/usr/bin/env bash
# Start MongoDB (Docker) and the microblog API on 127.0.0.1:8000 for Playwright API tests.
# Intended to be launched by Playwright's webServer (see playwright/playwright.config.ts).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required for Playwright API tests (MongoDB)." >&2
  exit 1
fi

if ! command -v pdm >/dev/null 2>&1; then
  echo "pdm is required to run the API for Playwright tests." >&2
  exit 1
fi

docker compose up -d mongo

echo "Waiting for MongoDB on 127.0.0.1:27017..."
for _ in $(seq 1 90); do
  if docker compose exec -T mongo mongosh --quiet --eval "db.runCommand({ ping: 1 }).ok" 2>/dev/null | grep -q "1"; then
    break
  fi
  sleep 1
done

export MONGODB_URI="${MONGODB_URI:-mongodb://127.0.0.1:27017}"
export MONGODB_DATABASE="${MONGODB_DATABASE:-microblog}"
export MONGODB_PING_ON_STARTUP="${MONGODB_PING_ON_STARTUP:-true}"
export MESSAGES_COLLECTION="${MESSAGES_COLLECTION:-messages}"

PORT="${PLAYWRIGHT_API_PORT:-18080}"
exec pdm run uvicorn agentic_test.api.app:app --host 127.0.0.1 --port "$PORT"
