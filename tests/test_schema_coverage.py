from dragonclaw.schema_extractor import extract_schema


def test_extracts_required_fields(fixture_source_dir):
    schema = extract_schema(fixture_source_dir, oc_version="2026.4.12")
    keys = {field.key for field in schema.fields}
    assert "provider" in keys
    assert "tools.elevated.enabled" in keys
    assert schema.metadata.oc_version == "2026.4.12"

