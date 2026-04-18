"""Regression: extractor must skip directories whose names match *.ts."""

import json
from pathlib import Path

from dragonclaw.schema_extractor import extract_schema


def test_skips_ts_named_directories(tmp_path: Path) -> None:
    weird = tmp_path / "ui" / "__screenshots__" / "navigation.browser.test.ts"
    weird.mkdir(parents=True)
    real = tmp_path / "real.ts"
    real.write_text("  foo: z.string()\n", encoding="utf-8")

    doc = extract_schema(tmp_path, oc_version="test")
    keys = {f.key for f in doc.fields}
    assert "foo" in keys


def test_json_schema_type_can_be_string_union(tmp_path: Path) -> None:
    """OpenClaw's openclaw.schema.json may use JSON Schema type unions (list of strings)."""
    schema = {
        "type": "object",
        "properties": {
            "foo": {
                "type": ["string", "object"],
                "properties": {"bar": {"type": "number"}},
            }
        },
    }
    (tmp_path / "openclaw.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    doc = extract_schema(tmp_path, oc_version="test")
    by_key = {f.key: f for f in doc.fields}
    assert "foo" in by_key
    assert by_key["foo"].field_type == "string|object"
    assert "foo.bar" in by_key
