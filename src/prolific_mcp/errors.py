from typing import Any


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""


def _extract_field_errors(body: Any) -> dict[str, list[str]] | None:
    """Pull field-level validation errors out of Prolific's error envelope, if present.

    Most Prolific API errors are wrapped as `{"error": {"detail": ..., ...}}`,
    where `detail` is a dict of field name -> list of messages for validation
    failures. At least one endpoint returns a bare `{"error": {"detail": "..."}}`
    without the rest of the envelope, and `detail` there is a plain string, not
    a field dict — this is treated as "no field errors" rather than guessed at.
    """
    if not isinstance(body, dict):
        return None
    error = body.get("error", body)
    if not isinstance(error, dict):
        return None
    detail = error.get("detail")
    if not isinstance(detail, dict) or not detail:
        return None
    if not all(isinstance(messages, list) for messages in detail.values()):
        return None
    return detail


def _format_message(status_code: int, body: Any, field_errors: dict[str, list[str]] | None) -> str:
    if field_errors:
        fields = "; ".join(
            f"{field}: {' '.join(str(message) for message in messages)}"
            for field, messages in field_errors.items()
        )
        return f"Prolific API validation error ({status_code}): {fields}"
    return f"Prolific API returned {status_code}: {body!r}"


class ProlificAPIError(Exception):
    """Raised when the Prolific API returns a non-2xx response.

    When the response body carries field-level validation errors (the
    common case for a 400), they're pulled out into `field_errors` and
    used to build a clear message instead of a raw repr of the whole body
    — the underlying `body` is still kept in full for anything that needs it.
    """

    def __init__(self, status_code: int, body: Any, message: str | None = None) -> None:
        self.status_code = status_code
        self.body = body
        self.field_errors = _extract_field_errors(body)
        super().__init__(message or _format_message(status_code, body, self.field_errors))
