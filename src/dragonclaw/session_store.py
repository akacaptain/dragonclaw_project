"""Persistent session state for runtime assistant."""

from __future__ import annotations

import json
from pathlib import Path

from dragonclaw.assistant import AssistantSessionState


def _session_file(workspace_dir: Path, session_id: str) -> Path:
    safe_session = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in session_id)
    return workspace_dir / ".dragonclaw" / "sessions" / f"{safe_session}.json"


def load_session_state(workspace_dir: Path, session_id: str) -> AssistantSessionState:
    workspace_dir = workspace_dir.expanduser().resolve()
    path = _session_file(workspace_dir, session_id)
    if not path.exists():
        return AssistantSessionState()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return AssistantSessionState(
        default_target_file=payload.get("default_target_file", "openclaw.json"),
        history=list(payload.get("history", [])),
    )


def save_session_state(workspace_dir: Path, session_id: str, state: AssistantSessionState) -> None:
    workspace_dir = workspace_dir.expanduser().resolve()
    path = _session_file(workspace_dir, session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "default_target_file": state.default_target_file,
                "history": state.history,
            },
            indent=2,
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )


def reset_session_state(workspace_dir: Path, session_id: str) -> bool:
    workspace_dir = workspace_dir.expanduser().resolve()
    path = _session_file(workspace_dir, session_id)
    if not path.exists():
        return False
    path.unlink()
    return True
