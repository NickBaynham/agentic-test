"""Harness-specific errors (fail closed, no secret leakage)."""


class HarnessError(Exception):
    """Base error for the AI API testing harness."""


class SandboxError(HarnessError):
    """Path or operation violates workspace sandbox rules."""


class HandwrittenEditError(HarnessError):
    """Attempted to modify a non-generated test file."""


class DockerComposeError(HarnessError):
    """Docker Compose invocation failed or was rejected."""
