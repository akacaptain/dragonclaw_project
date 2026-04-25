"""Runtime CLI for workspace config operations."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from dragonclaw.assistant import DragonClawAssistant
from dragonclaw.config_apply import apply_config_plan
from dragonclaw.config_surface import load_config_plan, verify_config_surface
from dragonclaw.session_store import load_session_state, reset_session_state, save_session_state

app = typer.Typer(help="DragonClaw runtime tools for OpenClaw workspaces")
session_app = typer.Typer(help="Inspect or reset persisted assistant sessions")
app.add_typer(session_app, name="session")
console = Console()


def _looks_like_workspace(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    if (path / "openclaw.json").exists():
        return True
    if (path / ".openclaw").exists():
        return True
    if (path / "auth").exists() and any((path / "auth").glob("**/*.json")):
        return True
    return False


def _detect_workspace(start: Path) -> Path | None:
    current = start.expanduser().resolve()
    if _looks_like_workspace(current):
        return current
    for parent in current.parents:
        if _looks_like_workspace(parent):
            return parent
    return None


def _resolve_workspace_dir(workspace_dir: Optional[Path]) -> Path:
    if workspace_dir is not None:
        resolved = workspace_dir.expanduser().resolve()
        if not resolved.exists() or not resolved.is_dir():
            raise typer.BadParameter(f"Workspace path does not exist or is not a directory: {resolved}")
        return resolved

    detected = _detect_workspace(Path.cwd())
    if detected is not None:
        return detected

    raw = typer.prompt("OpenClaw workspace path")
    prompted = Path(raw).expanduser().resolve()
    if not prompted.exists() or not prompted.is_dir():
        raise typer.BadParameter(f"Workspace path does not exist or is not a directory: {prompted}")
    return prompted


def _run_chat_loop(
    workspace_dir: Path,
    surface_path: Path,
    schema_path: Path,
    dry_run: bool,
    no_backup: bool,
    fail_on_unknown_files: bool,
    session_id: str,
) -> None:
    assistant = DragonClawAssistant()
    state = load_session_state(workspace_dir=workspace_dir, session_id=session_id)
    console.print(
        "[cyan]DragonClaw chat started[/cyan] "
        f"(session={session_id}, default_target={state.default_target_file}, dry_run={dry_run})"
    )
    console.print("Type 'exit' or 'quit' to end the session.")
    while True:
        raw = typer.prompt("you")
        message = raw.strip()
        if not message:
            continue
        if message.lower() in {"exit", "quit"}:
            save_session_state(workspace_dir=workspace_dir, session_id=session_id, state=state)
            console.print("[cyan]Session saved. Bye.[/cyan]")
            return
        try:
            result = assistant.handle(
                message=message,
                workspace_dir=workspace_dir,
                surface_path=surface_path,
                schema_path=schema_path,
                dry_run=dry_run,
                create_backups=not no_backup,
                fail_on_unknown_files=fail_on_unknown_files,
                session_state=state,
            )
            state = result.session_state
            save_session_state(workspace_dir=workspace_dir, session_id=session_id, state=state)
            console.print(f"[green]{result.summary}[/green]")
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    workspace_dir: Optional[Path] = typer.Option(None, help="OpenClaw workspace root (auto-detected when omitted)."),
    surface_path: Path = typer.Option(Path("artifacts/config_surface.json"), help="Discovered config surface."),
    schema_path: Path = typer.Option(Path("artifacts/schema.json"), help="Extracted schema."),
    dry_run: bool = typer.Option(True, help="Default: preview only. Use --no-dry-run to write files."),
    no_backup: bool = typer.Option(False, help="Disable .bak file creation before overwrite."),
    fail_on_unknown_files: bool = typer.Option(
        False,
        help="Fail if generated plans target files outside discovered config surface.",
    ),
    session_id: str = typer.Option("default", help="Persistent assistant session id."),
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    resolved_workspace = _resolve_workspace_dir(workspace_dir)
    _run_chat_loop(
        workspace_dir=resolved_workspace,
        surface_path=surface_path,
        schema_path=schema_path,
        dry_run=dry_run,
        no_backup=no_backup,
        fail_on_unknown_files=fail_on_unknown_files,
        session_id=session_id,
    )


@app.command("apply-config", hidden=True)
def apply_config_cmd(
    workspace_dir: Path,
    plan_path: Path = Path("artifacts/config_plan.json"),
    dry_run: bool = typer.Option(True, help="Default: preview only. Use --no-dry-run to write files."),
    no_backup: bool = typer.Option(False, help="Disable .bak file creation before overwrite."),
) -> None:
    plan = load_config_plan(plan_path)
    written = apply_config_plan(
        workspace_dir=workspace_dir,
        plan=plan,
        dry_run=dry_run,
        create_backups=not no_backup,
    )
    mode = "previewed" if dry_run else "written"
    console.print(f"[green]Config plan applied[/green]: {len(written)} files {mode}")


@app.command("verify-config-surface", hidden=True)
def verify_config_surface_cmd(
    workspace_dir: Path,
    surface_path: Path = Path("artifacts/config_surface.json"),
    fail_on_missing: bool = typer.Option(False, help="Exit with code 1 when expected files are missing."),
    fail_on_extra: bool = typer.Option(False, help="Exit with code 1 when extra JSON files are present."),
) -> None:
    report = verify_config_surface(surface_path=surface_path, workspace_dir=workspace_dir)
    expected = len(report["expected"])
    present = len(report["present"])
    missing = len(report["missing"])
    extra = len(report["extra"])
    console.print(
        f"[green]Config surface verification[/green]: "
        f"{present}/{expected} expected files present, {missing} missing, {extra} extra json files"
    )
    if missing:
        console.print("[yellow]Missing[/yellow]: " + ", ".join(report["missing"]))
    if extra:
        console.print("[yellow]Extra[/yellow]: " + ", ".join(report["extra"]))
    should_fail = (fail_on_missing and missing > 0) or (fail_on_extra and extra > 0)
    if should_fail:
        console.print("[red]Verification failed due to configured fail conditions.[/red]")
        raise typer.Exit(code=1)


@app.command("assist", hidden=True)
def assist_cmd(
    workspace_dir: Path,
    message: str = typer.Argument(..., help="Natural-language config request."),
    surface_path: Path = Path("artifacts/config_surface.json"),
    schema_path: Path = Path("artifacts/schema.json"),
    dry_run: bool = typer.Option(True, help="Default: preview only. Use --no-dry-run to write files."),
    no_backup: bool = typer.Option(False, help="Disable .bak file creation before overwrite."),
    fail_on_unknown_files: bool = typer.Option(
        False,
        help="Fail if a generated plan targets files outside discovered config surface.",
    ),
    session_id: str = typer.Option("default", help="Persistent assistant session id."),
) -> None:
    assistant = DragonClawAssistant()
    session_state = load_session_state(workspace_dir=workspace_dir, session_id=session_id)
    result = assistant.handle(
        message=message,
        workspace_dir=workspace_dir,
        surface_path=surface_path,
        schema_path=schema_path,
        dry_run=dry_run,
        create_backups=not no_backup,
        fail_on_unknown_files=fail_on_unknown_files,
        session_state=session_state,
    )
    save_session_state(workspace_dir=workspace_dir, session_id=session_id, state=result.session_state)
    console.print(f"[green]{result.summary}[/green]")
    console.print("Plan: " + str(sorted(result.plan.keys())))


@app.command("chat", hidden=True)
def chat_cmd(
    workspace_dir: Optional[Path] = None,
    surface_path: Path = Path("artifacts/config_surface.json"),
    schema_path: Path = Path("artifacts/schema.json"),
    dry_run: bool = typer.Option(True, help="Default: preview only. Use --no-dry-run to write files."),
    no_backup: bool = typer.Option(False, help="Disable .bak file creation before overwrite."),
    fail_on_unknown_files: bool = typer.Option(
        False,
        help="Fail if a generated plan targets files outside discovered config surface.",
    ),
    session_id: str = typer.Option("default", help="Persistent assistant session id."),
) -> None:
    resolved_workspace = _resolve_workspace_dir(workspace_dir)
    _run_chat_loop(
        workspace_dir=resolved_workspace,
        surface_path=surface_path,
        schema_path=schema_path,
        dry_run=dry_run,
        no_backup=no_backup,
        fail_on_unknown_files=fail_on_unknown_files,
        session_id=session_id,
    )


@session_app.command("show", hidden=True)
def session_show_cmd(
    workspace_dir: Path,
    session_id: str = typer.Option("default", help="Session id to inspect."),
) -> None:
    state = load_session_state(workspace_dir=workspace_dir, session_id=session_id)
    console.print(
        f"[green]Session[/green]: {session_id} "
        f"(default_target={state.default_target_file}, history_entries={len(state.history)})"
    )
    if state.history:
        tail = state.history[-5:]
        console.print("Recent messages:")
        for item in tail:
            console.print(f"- {item}")


@session_app.command("reset", hidden=True)
def session_reset_cmd(
    workspace_dir: Path,
    session_id: str = typer.Option("default", help="Session id to reset."),
) -> None:
    deleted = reset_session_state(workspace_dir=workspace_dir, session_id=session_id)
    if deleted:
        console.print(f"[green]Session reset[/green]: {session_id}")
    else:
        console.print(f"[yellow]No saved session found[/yellow]: {session_id}")
