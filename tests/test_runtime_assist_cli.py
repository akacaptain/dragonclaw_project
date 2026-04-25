import json
import os
from pathlib import Path

from typer.testing import CliRunner

from dragonclaw.runtime_cli import _resolve_workspace_dir, app


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
                ],
            }
        ),
        encoding="utf-8",
    )


def test_assist_cli_applies_message(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    surface_path = tmp_path / "config_surface.json"
    schema_path = tmp_path / "schema.json"
    _write_surface(surface_path)
    _write_schema(schema_path)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "assist",
            str(workspace),
            "set provider to openai",
            "--surface-path",
            str(surface_path),
            "--schema-path",
            str(schema_path),
            "--no-dry-run",
        ],
    )
    assert result.exit_code == 0
    config = json.loads((workspace / "openclaw.json").read_text(encoding="utf-8"))
    assert config["provider"] == "openai"


def test_default_command_starts_chat_and_quits(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    surface_path = tmp_path / "config_surface.json"
    schema_path = tmp_path / "schema.json"
    _write_surface(surface_path)
    _write_schema(schema_path)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "--workspace-dir",
            str(workspace),
            "--surface-path",
            str(surface_path),
            "--schema-path",
            str(schema_path),
        ],
        input="quit\n",
    )
    assert result.exit_code == 0
    assert "DragonClaw chat started" in result.output


def test_resolve_workspace_autodetects_current_directory(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "openclaw.json").write_text("{}", encoding="utf-8")
    old_cwd = Path.cwd()
    try:
        os.chdir(workspace)
        resolved = _resolve_workspace_dir(None)
    finally:
        os.chdir(old_cwd)
    assert resolved == workspace.resolve()


def test_assist_cli_persists_session_target_file(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    surface_path = tmp_path / "config_surface.json"
    schema_path = tmp_path / "schema.json"
    _write_surface(surface_path)
    _write_schema(schema_path)
    # Extend surface with auth file target for this test.
    surface = json.loads(surface_path.read_text(encoding="utf-8"))
    surface["files"].append({"path": "auth/profiles/default.json", "discovered_from": "src/config.ts", "required": False})
    surface_path.write_text(json.dumps(surface), encoding="utf-8")

    runner = CliRunner()
    first = runner.invoke(
        app,
        [
            "assist",
            str(workspace),
            "set token to abc in auth/profiles/default.json",
            "--surface-path",
            str(surface_path),
            "--schema-path",
            str(schema_path),
            "--no-dry-run",
            "--session-id",
            "test-session",
        ],
    )
    assert first.exit_code == 0

    second = runner.invoke(
        app,
        [
            "assist",
            str(workspace),
            "set name to default",
            "--surface-path",
            str(surface_path),
            "--schema-path",
            str(schema_path),
            "--no-dry-run",
            "--session-id",
            "test-session",
        ],
    )
    assert second.exit_code == 0
    profile = json.loads((workspace / "auth/profiles/default.json").read_text(encoding="utf-8"))
    assert profile["token"] == "abc"
    assert profile["name"] == "default"


def test_session_show_and_reset_commands(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    surface_path = tmp_path / "config_surface.json"
    schema_path = tmp_path / "schema.json"
    _write_surface(surface_path)
    _write_schema(schema_path)

    runner = CliRunner()
    assist = runner.invoke(
        app,
        [
            "assist",
            str(workspace),
            "set provider to openai",
            "--surface-path",
            str(surface_path),
            "--schema-path",
            str(schema_path),
            "--no-dry-run",
            "--session-id",
            "inspect-me",
        ],
    )
    assert assist.exit_code == 0

    show = runner.invoke(
        app,
        [
            "session",
            "show",
            str(workspace),
            "--session-id",
            "inspect-me",
        ],
    )
    assert show.exit_code == 0
    assert "history_entries=1" in show.output

    reset = runner.invoke(
        app,
        [
            "session",
            "reset",
            str(workspace),
            "--session-id",
            "inspect-me",
        ],
    )
    assert reset.exit_code == 0
    assert "Session reset" in reset.output
