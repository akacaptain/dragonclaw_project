import json

from typer.testing import CliRunner

from dragonclaw.runtime_cli import app


def test_verify_config_surface_can_fail_on_missing(tmp_path):
    surface_path = tmp_path / "config_surface.json"
    surface_path.write_text(
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
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "openclaw.json").write_text("{}", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "verify-config-surface",
            str(workspace),
            "--surface-path",
            str(surface_path),
            "--fail-on-missing",
        ],
    )
    assert result.exit_code == 1


def test_verify_config_surface_passes_without_fail_flags(tmp_path):
    surface_path = tmp_path / "config_surface.json"
    surface_path.write_text(
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
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "openclaw.json").write_text("{}", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "verify-config-surface",
            str(workspace),
            "--surface-path",
            str(surface_path),
        ],
    )
    assert result.exit_code == 0
