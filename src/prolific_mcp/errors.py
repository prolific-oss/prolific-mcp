from typing import Any


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""


class ProlificAPIError(Exception):
    """Raised when the Prolific API returns a non-2xx response."""

    def __init__(self, status_code: int, body: Any, message: str | None = None) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(message or f"Prolific API returned {status_code}: {body!r}")
