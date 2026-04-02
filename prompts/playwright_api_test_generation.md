# Playwright API test generation (Python sync `APIRequestContext`)

Use this checklist when authoring scenarios for `generate_api_test_from_scenario` (or when editing files under `generated/tests/`).

## Rules

1. **API only:** use `playwright.sync_api.sync_playwright` and `p.request.new_context(base_url=...)`. Never create `browser`, `page`, or UI locators.
2. **Base URL:** always read `API_BASE_URL` from the environment (the harness sets it when running pytest).
3. **Assertions:** assert HTTP status, then optionally `Content-Type` / JSON shape / required keys.
4. **Stability:** prefer explicit status codes and small JSON key checks over brittle full-body equality.
5. **Markers:** generated files should keep `pytestmark = pytest.mark.generated_api` so suites can filter with `-k generated_api`.

## Suggested scenario shape

- **Given** the service is reachable at `API_BASE_URL`
- **When** the client sends `<METHOD> <path>` (optional JSON body)
- **Then** the response status is `<code>` and the JSON includes keys: `...`

## Example mapping

| Scenario | endpoint | method | expected_status | response_json_keys |
| -------- | -------- | ------ | --------------- | ------------------ |
| Health probe | `/health` | GET | 200 | `["status"]` |
| OpenAPI contract | `/openapi.json` | GET | 200 | `["paths", "info"]` |
| Create resource | `/messages` | POST | 201 | `["id"]` |

## Editing workflow

1. Call `get_api_context` to pull OpenAPI from the running service.
2. Generate or hand-edit tests under `generated/tests/` only (handwritten tests live in `tests/handwritten_api/`).
3. Run `run_test` on a single file, then `run_all_generated_tests` for regression.
4. Use `get_test_artifacts` to inspect `junit.xml` / JSON report paths after a run.
