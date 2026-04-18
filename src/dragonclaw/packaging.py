"""Release artifact generation for DragonClaw pipeline outputs."""

from __future__ import annotations

import json
from pathlib import Path

from dragonclaw.models import SchemaDocument


def package_release(
    output_dir: Path,
    schema: SchemaDocument,
    training_data_path: Path,
    validation_report_path: Path | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": "dragonclaw",
        "oc_version": schema.metadata.oc_version,
        "schema_path": "schema/schema.json",
        "training_data_path": str(training_data_path),
        "validation_report_path": str(validation_report_path) if validation_report_path else None,
        "model_manifest": {
            "download_on_first_run": True,
            "cache_dir": "~/.dragonclaw/models",
        },
    }

    schema_dir = output_dir / "schema"
    schema_dir.mkdir(parents=True, exist_ok=True)
    (schema_dir / "schema.json").write_text(schema.model_dump_json(indent=2), encoding="utf-8")

    manifest_path = output_dir / "release-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path

