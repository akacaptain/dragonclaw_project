"""Error diagnosis helpers for config failures."""

from __future__ import annotations


def diagnose_error(message: str) -> str:
    lower = message.lower()
    if "expected array, received boolean" in lower:
        return "A config key that expects an array was set to boolean; convert it to a list."
    if "missing authentication header" in lower or "401" in lower:
        return "Provider authentication appears invalid or missing."
    return "Unable to classify error; inspect schema constraints and provider credentials."

