"""Runtime CLI for workspace config operations."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from dragonclaw.config_apply import apply_config_plan
from dragonclaw.config_surface import load_config_plan, verify_config_surface

app = typer.Typer(help="DragonClaw runtime tools for OpenClaw workspaces")
console = Console()


@app.command("apply-config")
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


@app.command("verify-config-surface")
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
