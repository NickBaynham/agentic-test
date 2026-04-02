"""Harness configuration (Pydantic v2)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class HarnessSettings(BaseModel):
    """Static settings for paths and defaults (no secrets)."""

    model_config = {"frozen": True}

    project_display_name: str = Field(default="agentic-test")
    default_api_base_url: str = Field(default="http://127.0.0.1:8000")
    health_path: str = Field(default="/health")
    openapi_path: str = Field(default="/openapi.json")
    generated_tests_subdir: str = Field(default="generated/tests")
    generated_history_subdir: str = Field(default="generated/history")
    generated_artifacts_subdir: str = Field(default="generated/artifacts/latest")
    generated_meta_subdir: str = Field(default="generated/tests/.meta")
    handwritten_tests_subdir: str = Field(default="tests/handwritten_api")
    compose_filename: str = Field(default="docker-compose.yml")
    allowed_compose_profiles: tuple[str, ...] = Field(default=("mongo", "full"))

    @field_validator("health_path", "openapi_path")
    @classmethod
    def path_must_start_with_slash(cls, v: str) -> str:
        if not v.startswith("/"):
            msg = "paths must be absolute within the URL (start with /)"
            raise ValueError(msg)
        return v


StackProfile = Literal["mongo", "full"]
