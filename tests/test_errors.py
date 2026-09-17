from prolific_mcp.errors import ProlificAPIError


def test_extracts_field_errors_from_wrapped_envelope() -> None:
    body = {
        "error": {
            "status": 400,
            "error_code": 140007,
            "detail": {"external_study_url": ["Enter a valid URL."]},
        }
    }

    error = ProlificAPIError(400, body)

    assert error.field_errors == {"external_study_url": ["Enter a valid URL."]}
    assert str(error) == (
        "Prolific API validation error (400): external_study_url: Enter a valid URL."
    )


def test_joins_multiple_fields_and_messages_in_message() -> None:
    body = {
        "error": {
            "detail": {
                "reward": ["Must be at least 100.", "Must be a whole number."],
                "total_available_places": ["Must be at least 1."],
            }
        }
    }

    error = ProlificAPIError(400, body)

    assert error.field_errors == {
        "reward": ["Must be at least 100.", "Must be a whole number."],
        "total_available_places": ["Must be at least 1."],
    }
    message = str(error)
    assert "reward: Must be at least 100. Must be a whole number." in message
    assert "total_available_places: Must be at least 1." in message


def test_falls_back_to_generic_message_when_detail_is_a_string() -> None:
    """At least one Prolific endpoint returns a bare envelope with a plain-string
    `detail` (e.g. a 409 conflict) rather than field-level validation errors."""
    body = {"error": {"detail": "This email is already in use."}}

    error = ProlificAPIError(409, body)

    assert error.field_errors is None
    assert str(error) == f"Prolific API returned 409: {body!r}"


def test_falls_back_to_generic_message_for_non_dict_body() -> None:
    error = ProlificAPIError(500, "server exploded")

    assert error.field_errors is None
    assert str(error) == "Prolific API returned 500: 'server exploded'"


def test_falls_back_to_generic_message_when_detail_is_empty() -> None:
    body: dict[str, object] = {"error": {"detail": {}}}

    error = ProlificAPIError(400, body)

    assert error.field_errors is None
    assert str(error) == f"Prolific API returned 400: {body!r}"


def test_explicit_message_overrides_generated_one() -> None:
    error = ProlificAPIError(400, {"error": {"detail": {"x": ["y"]}}}, message="custom")

    assert str(error) == "custom"
    assert error.field_errors == {"x": ["y"]}
