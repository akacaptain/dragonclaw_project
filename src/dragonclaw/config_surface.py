"""Discover OpenClaw config files from source references."""

from __future__ import annotations

import json
import re
from pathlib import Path

from dragonclaw.models import ConfigFileTarget, ConfigSurface, SchemaMetadata
from dragonclaw.schema_extractor import _hash_source

JSON_PATH_RE = re.compile(r"['\"]([^'\"]+\.json)['\"]")
LIKELY_CONFIG_RE = re.compile(r"(openclaw|config|auth|profile|credential|token)", re.IGNORECASE)


def _normalize_path(raw: str) -> str:
    value = raw.replace("\\", "/").strip()
    if value.startswith("./"):
        value = value[2:]
    return value


def _looks_like_config_json(path_value: str) -> bool:
    lowered = path_value.lower()
    if not lowered.endswith(".json"):
        return False
    return bool(LIKELY_CONFIG_RE.search(lowered))


def _collect_json_paths(source_path: Path) -> dict[str, str]:
    discovered: dict[str, str] = {}
    for path in source_path.rglob("*"):
        if not path.is_file() or path.suffix not in {".ts", ".tsx", ".js", ".mjs", ".cjs"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel_src = str(path.relative_to(source_path))
        for match in JSON_PATH_RE.finditer(text):
            raw = _normalize_path(match.group(1))
            if not _looks_like_config_json(raw):
                continue
            discovered.setdefault(raw, rel_src)
    return discovered


def discover_config_surface(source_path: Path, oc_version: str) -> ConfigSurface:
    source_path = source_path.expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"OpenClaw source path not found: {source_path}")

    discovered = _collect_json_paths(source_path)
    # Always include the baseline config file.
    discovered.setdefault("openclaw.json", "default")

    files = [
        ConfigFileTarget(path=path, discovered_from=discovered_from, required=(path == "openclaw.json"))
        for path, discovered_from in sorted(discovered.items())
    ]
    metadata = SchemaMetadata(
        oc_version=oc_version,
        source_hash=_hash_source(source_path),
        source_path=str(source_path),
    )
    return ConfigSurface(metadata=metadata, files=files)


def save_config_surface(surface: ConfigSurface, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(surface.model_dump_json(indent=2), encoding="utf-8")


def load_config_surface(path: Path) -> ConfigSurface:
    return ConfigSurface.model_validate_json(path.read_text(encoding="utf-8"))


def load_config_plan(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Config plan must be a JSON object mapping file paths to JSON objects.")
    normalized: dict[str, dict] = {}
    for file_path, payload in data.items():
        if not isinstance(file_path, str) or not isinstance(payload, dict):
            raise ValueError("Config plan entries must be of shape {\"relative/path.json\": {...}}.")
        normalized[_normalize_path(file_path)] = payload
    return normalized


def verify_config_surface(surface_path: Path, workspace_dir: Path) -> dict[str, list[str]]:
    surface = load_config_surface(surface_path)
    workspace_dir = workspace_dir.expanduser().resolve()
    expected = sorted({_normalize_path(item.path) for item in surface.files})
    expected_set = set(expected)

    present: list[str] = []
    missing: list[str] = []
    for rel in expected:
        if (workspace_dir / rel).exists():
            present.append(rel)
        else:
            missing.append(rel)

    extra: list[str] = []
    for path in workspace_dir.rglob("*.json"):
        if not path.is_file():
            continue
        rel = _normalize_path(str(path.relative_to(workspace_dir)))
        if rel not in expected_set:
            extra.append(rel)

    return {
        "expected": expected,
        "present": sorted(present),
        "missing": sorted(missing),
        "extra": sorted(extra),
    }
