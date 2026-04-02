"""FastMCP server exposing the API testing harness (stdio transport)."""

from __future__ import annotations

import logging
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from agentic_test.ai_api_tester.handlers import ApiTestHarness, handle_tool_error

logger = logging.getLogger(__name__)


def build_mcp_app() -> FastMCP:
    """Create FastMCP app with all tools registered."""
    mcp = FastMCP(
        "agentic-api-tester",
        instructions=(
            "API testing harness for a Dockerized microservice. "
            "Use tools to introspect OpenAPI, generate Playwright APIRequestContext tests "
            "under generated/tests/, run pytest, and manage docker compose (allow-listed)."
        ),
    )
    harness = ApiTestHarness()

    @mcp.tool()
    def get_service_info(api_base_url: str | None = None) -> str:
        """Return project name, default base URL, and health endpoint status."""
        try:
            return harness.get_service_info(api_base_url)
        except Exception as e:  # noqa: BLE001
            logger.exception("get_service_info failed")
            return handle_tool_error(e)

    @mcp.tool()
    def get_api_context(api_base_url: str | None = None) -> str:
        """Fetch OpenAPI JSON (or transport errors) from the target service."""
        try:
            return harness.get_api_context(api_base_url)
        except Exception as e:  # noqa: BLE001
            logger.exception("get_api_context failed")
            return handle_tool_error(e)

    @mcp.tool()
    def list_tests() -> str:
        """List handwritten (tests/handwritten_api) and generated (generated/tests) API tests."""
        try:
            return harness.list_tests()
        except Exception as e:  # noqa: BLE001
            logger.exception("list_tests failed")
            return handle_tool_error(e)

    @mcp.tool()
    def read_test_file(relative_path: str) -> str:
        """Read a test file from allowed directories (path relative to repo root)."""
        try:
            return harness.read_test_file(relative_path)
        except Exception as e:  # noqa: BLE001
            logger.exception("read_test_file failed")
            return handle_tool_error(e)

    @mcp.tool()
    def update_generated_test(relative_path: str, content: str) -> str:
        """Update a file under generated/tests only; copies prior version to generated/history."""
        try:
            return harness.update_generated_test(relative_path, content)
        except Exception as e:  # noqa: BLE001
            logger.exception("update_generated_test failed")
            return handle_tool_error(e)

    @mcp.tool()
    def delete_generated_test(relative_path: str) -> str:
        """Delete a generated test under generated/tests only."""
        try:
            return harness.delete_generated_test(relative_path)
        except Exception as e:  # noqa: BLE001
            logger.exception("delete_generated_test failed")
            return handle_tool_error(e)

    @mcp.tool()
    def generate_api_test_from_scenario(
        scenario: str,
        endpoint: str,
        http_method: str,
        expected_status: int,
        response_json_keys: list[str] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a pytest module using Playwright sync APIRequestContext only.
        Saves under generated/tests/ with sidecar metadata in generated/tests/.meta/.
        """
        try:
            return harness.generate_api_test_from_scenario(
                scenario=scenario,
                endpoint=endpoint,
                http_method=http_method,
                expected_status=expected_status,
                response_json_keys=response_json_keys,
                json_body=json_body,
            )
        except Exception as e:  # noqa: BLE001
            logger.exception("generate_api_test_from_scenario failed")
            return handle_tool_error(e)

    @mcp.tool()
    def run_test(relative_path: str, api_base_url: str | None = None) -> str:
        """Run pytest on one file; writes junit + JSON report under generated/artifacts/latest."""
        try:
            return harness.run_test(relative_path, api_base_url=api_base_url)
        except Exception as e:  # noqa: BLE001
            logger.exception("run_test failed")
            return handle_tool_error(e)

    @mcp.tool()
    def run_all_generated_tests(
        api_base_url: str | None = None,
        tag_filter: str | None = None,
    ) -> str:
        """Run pytest on generated/tests (optional -k expression, e.g. marker name)."""
        try:
            return harness.run_all_generated_tests(
                api_base_url=api_base_url,
                tag_filter=tag_filter,
            )
        except Exception as e:  # noqa: BLE001
            logger.exception("run_all_generated_tests failed")
            return handle_tool_error(e)

    @mcp.tool()
    def get_test_artifacts() -> str:
        """List result files from the latest pytest run (generated/artifacts/latest)."""
        try:
            return harness.get_test_artifacts()
        except Exception as e:  # noqa: BLE001
            logger.exception("get_test_artifacts failed")
            return handle_tool_error(e)

    @mcp.tool()
    def start_target_stack(profile: str) -> str:
        """Start allow-listed Docker Compose stack: profile 'mongo' or 'full'."""
        try:
            return harness.start_target_stack(profile)
        except Exception as e:  # noqa: BLE001
            logger.exception("start_target_stack failed")
            return handle_tool_error(e)

    @mcp.tool()
    def stop_target_stack() -> str:
        """Run docker compose down for the repository compose file."""
        try:
            return harness.stop_target_stack()
        except Exception as e:  # noqa: BLE001
            logger.exception("stop_target_stack failed")
            return handle_tool_error(e)

    return mcp


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    app = build_mcp_app()
    try:
        app.run()
    except KeyboardInterrupt:
        # Normal when stopping the stdio server from a terminal (Ctrl+C). Avoids
        # propagating into asyncio/anyio shutdown, which can print long tracebacks
        # or fatal stdin-lock errors if SIGINT is sent repeatedly during teardown.
        logger.info("MCP server stopped (interrupt).")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
