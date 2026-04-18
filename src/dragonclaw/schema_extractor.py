"""Schema extraction from OpenClaw source trees."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from dragonclaw.models import SchemaDocument, SchemaField, SchemaMetadata

ZOD_FIELD_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_\-]*)\s*:\s*z\.")


def _hash_source(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(root)).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _flatten_json_schema(node: dict[str, Any], prefix: str = "") -> list[SchemaField]:
    props = node.get("properties", {})
    required = set(node.get("required", []))
    fields: list[SchemaField] = []
    for key, spec in props.items():
        full_key = f"{prefix}.{key}" if prefix else key
        field_type = spec.get("type", "unknown")
        enum_values = [str(v) for v in spec.get("enum", [])]
        default = spec.get("default")
        fields.append(
            SchemaField(
                key=full_key,
                field_type=field_type,
                required=key in required,
                default=default,
                enum_values=enum_values,
                constraints={k: v for k, v in spec.items() if k not in {"type", "enum", "default", "properties", "required"}},
            )
        )
        if field_type == "object":
            fields.extend(_flatten_json_schema(spec, full_key))
    return fields


def extract_schema(source_path: Path, oc_version: str) -> SchemaDocument:
    source_path = source_path.expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"OpenClaw source path not found: {source_path}")

    schema_candidates = [
        source_path / "openclaw.schema.json",
        source_path / "schema.json",
    ]
    json_schema_path = next((p for p in schema_candidates if p.exists()), None)

    fields: list[SchemaField] = []
    if json_schema_path:
        parsed = json.loads(json_schema_path.read_text(encoding="utf-8"))
        fields = _flatten_json_schema(parsed)
    else:
        seen: set[str] = set()
        for path in source_path.rglob("*.ts"):
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                match = ZOD_FIELD_RE.match(line)
                if not match:
                    continue
                key = match.group(1)
                if key in seen:
                    continue
                seen.add(key)
                fields.append(SchemaField(key=key, field_type="unknown", required=False))

    metadata = SchemaMetadata(
        oc_version=oc_version,
        source_hash=_hash_source(source_path),
        source_path=str(source_path),
    )
    return SchemaDocument(metadata=metadata, fields=sorted(fields, key=lambda item: item.key))

