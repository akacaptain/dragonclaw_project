"""Chat-first assistant runtime for OpenClaw config changes."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dragonclaw.config_apply import apply_config_plan
from dragonclaw.config_surface import load_config_surface
from dragonclaw.io_utils import load_schema
from dragonclaw.validator import validate_patch

SET_RE = re.compile(r"^\s*set\s+([a-zA-Z0-9_.-]+)\s*(?:to|=)\s*(.+?)\s*$", re.IGNORECASE)
ENABLE_RE = re.compile(r"^\s*enable\s+([a-zA-Z0-9_.-]+)\s*$", re.IGNORECASE)
DISABLE_RE = re.compile(r"^\s*disable\s+([a-zA-Z0-9_.-]+)\s*$", re.IGNORECASE)
USE_PROVIDER_RE = re.compile(r"^\s*(?:use\s+|set\s+provider\s*(?:to|=)\s*)(anthropic|openai|groq|openrouter)\s*$", re.IGNORECASE)
MODEL_RE = re.compile(r"^\s*(?:set\s+)?model\s*(?:to|=)?\s*([A-Za-z0-9_./:-]+)\s*$", re.IGNORECASE)
TARGET_FILE_RE = re.compile(r"(?:in|for)\s+([^\s]+\.json)\b", re.IGNORECASE)
JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.IGNORECASE | re.DOTALL)


@dataclass
class AssistantResult:
    plan: dict[str, dict[str, Any]]
    written_files: list[Path]
    dry_run: bool
    summary: str
    session_state: "AssistantSessionState"


@dataclass
class AssistantSessionState:
    default_target_file: str = "openclaw.json"
    history: list[str] = field(default_factory=list)


def _set_path(root: dict[str, Any], dotted_key: str, value: Any) -> None:
    cursor = root
    parts = dotted_key.split(".")
    for key in parts[:-1]:
        existing = cursor.get(key)
        if not isinstance(existing, dict):
            cursor[key] = {}
        cursor = cursor[key]
    cursor[parts[-1]] = value


def _parse_scalar(raw: str) -> Any:
    value = raw.strip().strip("\"'")
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _extract_plan_from_json_block(message: str) -> dict[str, dict[str, Any]] | None:
    match = JSON_BLOCK_RE.search(message)
    if not match:
        return None
    payload = json.loads(match.group(1))
    if not isinstance(payload, dict):
        raise ValueError("JSON plan must be an object.")
    normalized: dict[str, dict[str, Any]] = {}
    for file_path, patch in payload.items():
        if not isinstance(file_path, str) or not isinstance(patch, dict):
            raise ValueError("JSON plan must map file paths to JSON objects.")
        normalized[file_path] = patch
    return normalized


def _extract_target_file(message: str, default_target_file: str) -> tuple[str, str]:
    target_match = TARGET_FILE_RE.search(message)
    if not target_match:
        return default_target_file, message
    target_file = target_match.group(1)
    cleaned = TARGET_FILE_RE.sub("", message).strip()
    return target_file, cleaned


def _build_plan_from_text(message: str, default_target_file: str = "openclaw.json") -> dict[str, dict[str, Any]]:
    explicit = _extract_plan_from_json_block(message)
    if explicit is not None:
        return explicit

    target_file, normalized_message = _extract_target_file(message, default_target_file)
    patch: dict[str, Any] = {}

    for clause in re.split(r"\s+\band\b\s+", normalized_message, flags=re.IGNORECASE):
        set_match = SET_RE.search(clause)
        if set_match:
            _set_path(patch, set_match.group(1), _parse_scalar(set_match.group(2)))
            continue

        enable_match = ENABLE_RE.search(clause)
        if enable_match:
            _set_path(patch, enable_match.group(1), True)
            continue

        disable_match = DISABLE_RE.search(clause)
        if disable_match:
            _set_path(patch, disable_match.group(1), False)
            continue

        provider_match = USE_PROVIDER_RE.search(clause)
        if provider_match:
            patch["provider"] = provider_match.group(1).lower()
            continue

        model_match = MODEL_RE.search(clause)
        if model_match:
            patch["model"] = model_match.group(1)
            continue

    if not patch:
        raise ValueError(
            "I could not derive config changes from that message. "
            "Try 'set provider to openai', 'enable tools.elevated.enabled', or provide a ```json``` plan."
        )

    return {target_file: patch}


def _summarize(plan: dict[str, dict[str, Any]], dry_run: bool, written_files: list[Path]) -> str:
    mode = "Previewed" if dry_run else "Applied"
    file_count = len(written_files)
    targets = ", ".join(sorted(plan.keys()))
    return f"{mode} config changes for {file_count} file(s): {targets}"


class DragonClawAssistant:
    def handle(
        self,
        message: str,
        workspace_dir: Path,
        surface_path: Path = Path("artifacts/config_surface.json"),
        schema_path: Path = Path("artifacts/schema.json"),
        dry_run: bool = True,
        create_backups: bool = True,
        fail_on_unknown_files: bool = False,
        validate_openclaw_patch: bool = True,
        session_state: AssistantSessionState | None = None,
    ) -> AssistantResult:
        state = session_state or AssistantSessionState()
        plan = _build_plan_from_text(message, default_target_file=state.default_target_file)
        workspace_dir = workspace_dir.expanduser().resolve()

        surface = load_config_surface(surface_path)
        allowed = {item.path for item in surface.files}
        unknown_files = sorted(path for path in plan.keys() if path not in allowed)
        if fail_on_unknown_files and unknown_files:
            raise ValueError(f"Plan targets files outside discovered config surface: {', '.join(unknown_files)}")

        if validate_openclaw_patch and "openclaw.json" in plan and schema_path.exists():
            schema = load_schema(schema_path)
            valid, invalid_keys = validate_patch(schema, plan["openclaw.json"])
            if not valid:
                raise ValueError(f"Patch contains invalid openclaw.json keys: {', '.join(invalid_keys)}")

        written = apply_config_plan(
            workspace_dir=workspace_dir,
            plan=plan,
            dry_run=dry_run,
            create_backups=create_backups,
        )
        if len(plan) == 1:
            state.default_target_file = next(iter(plan.keys()))
        state.history.append(message)
        return AssistantResult(
            plan=plan,
            written_files=written,
            dry_run=dry_run,
            summary=_summarize(plan, dry_run=dry_run, written_files=written),
            session_state=state,
        )
