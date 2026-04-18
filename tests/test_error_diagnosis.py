from dragonclaw.diagnostics import diagnose_error


def test_known_error_mapping():
    msg = "Config invalid - tools.elevated.allowFrom.telegram: Invalid input: expected array, received boolean"
    diagnosis = diagnose_error(msg)
    assert "expects an array" in diagnosis

