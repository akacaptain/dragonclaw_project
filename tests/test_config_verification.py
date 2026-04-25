import json

from dragonclaw.config_surface import verify_config_surface


def test_verify_config_surface_reports_missing_and_extra(tmp_path):
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
    (workspace / "random.json").write_text("{}", encoding="utf-8")

    report = verify_config_surface(surface_path=surface_path, workspace_dir=workspace)

    assert "openclaw.json" in report["present"]
    assert "auth/profiles/default.json" in report["missing"]
    assert "random.json" in report["extra"]
