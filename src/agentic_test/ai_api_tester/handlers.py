"""MCP tool implementations (typed, JSON-serializable outputs)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agentic_test.ai_api_tester import docker_manager as docker_mgr
from agentic_test.ai_api_tester.config import HarnessSettings
from agentic_test.ai_api_tester.errors import HarnessError
from agentic_test.ai_api_tester.generator import (
    build_generation_metadata,
    build_playwright_api_test_module,
)
from agentic_test.ai_api_tester.introspection import fetch_health, fetch_openapi_json
from agentic_test.ai_api_tester.paths import find_repo_root
from agentic_test.ai_api_tester.runner import run_pytest_targets
from agentic_test.ai_api_tester.workspace import (
    delete_generated_test,
    list_test_files,
    read_allowed_test_file,
    update_generated_test_content,
    write_generated_test,
)
from agentic_test.ai_api_tester.workspace import (
    ensure_artifacts_dir as ws_artifacts,
)


def _dump(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


class ApiTestHarness:
    """Facade used by the MCP server (and unit tests)."""

    def __init__(
        self,
        repo_root: Path | None = None,
        settings: HarnessSettings | None = None,
    ) -> None:
        self.repo_root = repo_root or find_repo_root()
        self.settings = settings or HarnessSettings()

    def get_service_info(self, api_base_url: str | None = None) -> str:
        base = api_base_url or str(self.settings.default_api_base_url)
        health = fetch_health(base, self.settings)
        return _dump(
            {
                "project_name": self.settings.project_display_name,
                "default_api_base_url": str(self.settings.default_api_base_url),
                "requested_base_url": base,
                "health_path": self.settings.health_path,
                "health_check": health,
            },
        )

    def get_api_context(self, api_base_url: str | None = None) -> str:
        base = api_base_url or str(self.settings.default_api_base_url)
        openapi = fetch_openapi_json(base, self.settings)
        return _dump({"base_url": base, "openapi_fetch": openapi})

    def list_tests(self) -> str:
        handwritten, generated = list_test_files(self.repo_root, self.settings)
        return _dump(
            {
                "handwritten": [str(p.relative_to(self.repo_root)) for p in handwritten],
                "generated": [str(p.relative_to(self.repo_root)) for p in generated],
            },
        )

    def read_test_file(self, relative_path: str) -> str:
        p = read_allowed_test_file(self.repo_root, relative_path, self.settings)
        stat = p.stat()
        return _dump(
            {
                "path": str(p.relative_to(self.repo_root)),
                "size_bytes": stat.st_size,
                "content": p.read_text(encoding="utf-8"),
            },
        )

    def update_generated_test(self, relative_path: str, content: str) -> str:
        p = update_generated_test_content(self.repo_root, relative_path, content, self.settings)
        return _dump(
            {
                "ok": True,
                "path": str(p.relative_to(self.repo_root)),
                "message": "Updated; previous revision copied to generated/history/.",
            },
        )

    def delete_generated_test(self, relative_path: str) -> str:
        delete_generated_test(self.repo_root, relative_path, self.settings)
        return _dump({"ok": True, "path": relative_path, "message": "Deleted if it existed."})

    def generate_api_test_from_scenario(
        self,
        scenario: str,
        endpoint: str,
        http_method: str,
        expected_status: int,
        response_json_keys: list[str] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> str:
        allowed = {"GET", "POST", "PATCH", "DELETE", "PUT"}
        hm = http_method.strip().upper()
        if hm not in allowed:
            msg = f"http_method must be one of {sorted(allowed)}"
            raise ValueError(msg)
        fname, source = build_playwright_api_test_module(
            scenario=scenario,
            endpoint=endpoint,
            http_method=hm,  # type: ignore[arg-type]
            expected_status=expected_status,
            response_json_keys=response_json_keys,
            json_body=json_body,
        )
        rel = f"{self.settings.generated_tests_subdir}/{fname}"
        meta = build_generation_metadata(
            scenario=scenario,
            endpoint=endpoint,
            http_method=hm,
            expected_status=expected_status,
            response_json_keys=response_json_keys,
        )
        write_generated_test(self.repo_root, rel, source, self.settings, metadata=meta)
        return _dump(
            {
                "ok": True,
                "relative_path": rel,
                "filename": fname,
                "preview": source[:2000],
            },
        )

    def run_test(
        self,
        relative_path: str,
        api_base_url: str | None = None,
    ) -> str:
        p = read_allowed_test_file(self.repo_root, relative_path, self.settings)
        env: dict[str, str] = {}
        if api_base_url:
            env["API_BASE_URL"] = api_base_url
        summary = run_pytest_targets(
            [p],
            repo_root=self.repo_root,
            settings=self.settings,
            extra_env=env or None,
        )
        return _dump(summary)

    def run_all_generated_tests(
        self,
        api_base_url: str | None = None,
        tag_filter: str | None = None,
    ) -> str:
        gen_dir = self.repo_root / self.settings.generated_tests_subdir
        if not gen_dir.is_dir():
            return _dump({"passed": False, "detail": "generated/tests does not exist."})
        env: dict[str, str] = {}
        if api_base_url:
            env["API_BASE_URL"] = api_base_url
        kw = tag_filter.strip() if tag_filter else None
        summary = run_pytest_targets(
            [gen_dir],
            repo_root=self.repo_root,
            settings=self.settings,
            extra_env=env or None,
            keyword_expression=kw,
        )
        return _dump(summary)

    def get_test_artifacts(self) -> str:
        art = ws_artifacts(self.repo_root, self.settings)
        files = sorted(art.iterdir()) if art.is_dir() else []
        return _dump(
            {
                "artifacts_dir": str(art.relative_to(self.repo_root)),
                "files": [f.name for f in files if f.is_file()],
            },
        )

    def start_target_stack(self, profile: str) -> str:
        if profile not in ("mongo", "full"):
            msg = "profile must be 'mongo' or 'full'"
            raise ValueError(msg)
        data = docker_mgr.start_target_stack(
            profile,  # type: ignore[arg-type]
            repo_root=self.repo_root,
            settings=self.settings,
        )
        return _dump(data)

    def stop_target_stack(self) -> str:
        data = docker_mgr.stop_target_stack(repo_root=self.repo_root, settings=self.settings)
        return _dump(data)


def handle_tool_error(e: Exception) -> str:
    """Stable JSON error payload (no secrets)."""
    if isinstance(e, (HarnessError, ValueError)):
        return _dump({"ok": False, "error": type(e).__name__, "message": str(e)})
    return _dump(
        {
            "ok": False,
            "error": type(e).__name__,
            "message": "An unexpected error occurred.",
        },
    )
