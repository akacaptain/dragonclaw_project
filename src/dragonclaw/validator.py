"""Validation layer for generated config patches."""

from __future__ import annotations

from typing import Any

from dragonclaw.models import SchemaDocument


def _flatten_patch(data: dict[str, Any], prefix: str = "") -> set[str]:
    keys: set[str] = set()
    for key, value in data.items():
        full = f"{prefix}.{key}" if prefix else key
        keys.add(full)
        if isinstance(value, dict):
            keys.update(_flatten_patch(value, full))
    return keys


def validate_patch(schema: SchemaDocument, patch: dict[str, Any]) -> tuple[bool, list[str]]:
    schema_keys = set(schema.field_map().keys())
    patch_keys = _flatten_patch(patch)
    invalid = sorted(k for k in patch_keys if k not in schema_keys and not any(sk.startswith(f"{k}.") for sk in schema_keys))
    return len(invalid) == 0, invalid

