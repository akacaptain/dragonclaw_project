import json

from dragonclaw.config_surface import discover_config_surface, load_config_plan


def test_discovers_config_files_from_source(tmp_path):
    src = tmp_path / "openclaw-src"
    src.mkdir()
    (src / "config.ts").write_text(
        """
const MAIN = "openclaw.json";
const PROFILE = "auth/profiles/default.json";
const TOKENS = "./auth/tokens.json";
""",
        encoding="utf-8",
    )

    surface = discover_config_surface(src, oc_version="test")
    paths = {f.path for f in surface.files}
    assert "openclaw.json" in paths
    assert "auth/profiles/default.json" in paths
    assert "auth/tokens.json" in paths


def test_load_config_plan_requires_object_values(tmp_path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps({"openclaw.json": {"provider": "openai"}}), encoding="utf-8")

    plan = load_config_plan(plan_path)
    assert plan["openclaw.json"]["provider"] == "openai"
