"""Apply a multi-file OpenClaw config plan to disk."""

from __future__ import annotations

import json
from pathlib import Path

from dragonclaw.configurator import merge_patch


def _read_json_file(path: Path) -> dict:
    if not path.exists():
        return {}
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"Existing file is not a JSON object: {path}")
    return loaded


def apply_config_plan(
    workspace_dir: Path,
    plan: dict[str, dict],
    dry_run: bool = False,
    create_backups: bool = True,
) -> list[Path]:
    workspace_dir = workspace_dir.expanduser().resolve()
    workspace_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for rel_path, patch in sorted(plan.items()):
        target = (workspace_dir / rel_path).resolve()
        if workspace_dir not in {target, *target.parents}:
            raise ValueError(f"Refusing to write outside workspace: {target}")
        if not target.suffix == ".json":
            raise ValueError(f"Only .json targets are supported: {rel_path}")

        current = _read_json_file(target)
        merged = merge_patch(current, patch)
        written.append(target)

        if dry_run:
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        if create_backups and target.exists():
            backup = target.with_suffix(target.suffix + ".bak")
            backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
        target.write_text(json.dumps(merged, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    return written
