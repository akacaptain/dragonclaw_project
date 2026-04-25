import json

from dragonclaw.assistant import AssistantSessionState, DragonClawAssistant


def _write_surface(path):
    path.write_text(
        json.dumps(
            {
                "metadata": {
                    "oc_version": "test",
                    "extracted_at": "2026-01-01T00:00:00+00:00",
                    "source_hash": "abc",
                    "source_path": "/tmp/source",
                },
                "files": [
                    {"path": "openclaw.json", "discovered_from": "default", "required": True},
                    {"path": "auth/profiles/default.json", "discovered_from": "src/config.ts", "required": False},
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_schema(path):
    path.write_text(
        json.dumps(
            {
                "metadata": {
                    "oc_version": "test",
                    "extracted_at": "2026-01-01T00:00:00+00:00",
                    "source_hash": "abc",
                    "source_path": "/tmp/source",
                },
                "fields": [
                    {"key": "provider", "field_type": "string", "required": False},
                    {"key": "model", "field_type": "string", "required": False},
                    {"key": "tools", "field_type": "object", "required": False},
                    {"key": "tools.elevated", "field_type": "object", "required": False},
                    {"key": "tools.elevated.enabled", "field_type": "boolean", "required": False},
                ],
            }
        ),
        encoding="utf-8",
    )


def test_assistant_applies_simple_message(tmp_path):
    surface_path = tmp_path / "config_surface.json"
    schema_path = tmp_path / "schema.json"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write_surface(surface_path)
    _write_schema(schema_path)

    assistant = DragonClawAssistant()
    result = assistant.handle(
        message="set provider to openai and enable tools.elevated.enabled",
        workspace_dir=workspace,
        surface_path=surface_path,
        schema_path=schema_path,
        dry_run=False,
    )
    assert "Applied config changes" in result.summary
    written = json.loads((workspace / "openclaw.json").read_text(encoding="utf-8"))
    assert written["provider"] == "openai"
    assert written["tools"]["elevated"]["enabled"] is True


def test_assistant_rejects_invalid_openclaw_keys(tmp_path):
    surface_path = tmp_path / "config_surface.json"
    schema_path = tmp_path / "schema.json"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write_surface(surface_path)
    _write_schema(schema_path)

    assistant = DragonClawAssistant()
    try:
        assistant.handle(
            message="set fakeKeyThatDoesNotExist to true",
            workspace_dir=workspace,
            surface_path=surface_path,
            schema_path=schema_path,
            dry_run=True,
        )
    except ValueError as exc:
        assert "invalid openclaw.json keys" in str(exc)
    else:
        raise AssertionError("Expected invalid schema key error")


def test_assistant_supports_json_plan_for_multiple_files(tmp_path):
    surface_path = tmp_path / "config_surface.json"
    schema_path = tmp_path / "schema.json"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write_surface(surface_path)
    _write_schema(schema_path)

    assistant = DragonClawAssistant()
    msg = """apply this
```json
{
  "openclaw.json": {"provider": "groq"},
  "auth/profiles/default.json": {"token": "abc"}
}
```"""
    result = assistant.handle(
        message=msg,
        workspace_dir=workspace,
        surface_path=surface_path,
        schema_path=schema_path,
        dry_run=False,
    )
    assert len(result.written_files) == 2
    profile = json.loads((workspace / "auth/profiles/default.json").read_text(encoding="utf-8"))
    assert profile["token"] == "abc"


def test_assistant_uses_session_default_target_file(tmp_path):
    surface_path = tmp_path / "config_surface.json"
    schema_path = tmp_path / "schema.json"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write_surface(surface_path)
    _write_schema(schema_path)

    assistant = DragonClawAssistant()
    state = AssistantSessionState(default_target_file="auth/profiles/default.json")
    result = assistant.handle(
        message="set token to abc",
        workspace_dir=workspace,
        surface_path=surface_path,
        schema_path=schema_path,
        dry_run=False,
        session_state=state,
        validate_openclaw_patch=False,
    )
    assert "auth/profiles/default.json" in result.plan
    profile = json.loads((workspace / "auth/profiles/default.json").read_text(encoding="utf-8"))
    assert profile["token"] == "abc"
