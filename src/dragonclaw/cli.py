"""Maintainer CLI for DragonClaw build pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from dragonclaw.evaluation import validate_samples
from dragonclaw.fine_tune import run_fine_tune
from dragonclaw.io_utils import (
    load_schema,
    load_training_data,
    save_schema,
    save_training_data,
    save_validation_report,
)
from dragonclaw.models import TrainConfig
from dragonclaw.packaging import package_release
from dragonclaw.schema_extractor import extract_schema
from dragonclaw.training_data import generate_training_samples

app = typer.Typer(help="DragonClaw maintainer pipeline CLI")
console = Console()


@app.command("extract-schema")
def extract_schema_cmd(source_path: Path, output: Path = Path("artifacts/schema.json"), oc_version: str = "unknown") -> None:
    schema = extract_schema(source_path=source_path, oc_version=oc_version)
    save_schema(schema, output)
    console.print(f"[green]Schema extracted[/green]: {output} ({len(schema.fields)} fields)")


@app.command("generate-training")
def generate_training_cmd(
    schema_path: Path = Path("artifacts/schema.json"),
    output: Path = Path("artifacts/training_data.jsonl"),
    seed: int = 42,
) -> None:
    schema = load_schema(schema_path)
    samples = generate_training_samples(schema, seed=seed)
    save_training_data(samples, output)
    console.print(f"[green]Training data generated[/green]: {output} ({len(samples)} rows)")


@app.command("fine-tune")
def fine_tune_cmd(
    dataset_path: Path = Path("artifacts/training_data.jsonl"),
    output_dir: Path = Path("artifacts/model"),
    base_model: str = "meta-llama/Llama-3.2-3B-Instruct",
    backend: str = "hf-peft",
    dry_run: bool = True,
) -> None:
    config = TrainConfig(
        base_model=base_model,
        dataset_path=str(dataset_path),
        output_dir=str(output_dir),
        backend=backend,  # type: ignore[arg-type]
        dry_run=dry_run,
    )
    result = run_fine_tune(config)
    console.print(f"[green]Fine-tune stage[/green]: {result}")


@app.command("validate-model")
def validate_model_cmd(
    schema_path: Path = Path("artifacts/schema.json"),
    training_data_path: Path = Path("artifacts/training_data.jsonl"),
    output: Path = Path("artifacts/validation_report.json"),
    max_cases: Optional[int] = None,
) -> None:
    schema = load_schema(schema_path)
    data = load_training_data(training_data_path)
    report = validate_samples(schema, data, max_cases=max_cases)
    save_validation_report(report, output)
    console.print(
        f"[green]Validation complete[/green]: {output} "
        f"({report.passed_cases}/{report.total_cases}, {report.coverage_percent}%)"
    )


@app.command("package")
def package_cmd(
    schema_path: Path = Path("artifacts/schema.json"),
    training_data_path: Path = Path("artifacts/training_data.jsonl"),
    validation_report_path: Path = Path("artifacts/validation_report.json"),
    output_dir: Path = Path("dist/release"),
) -> None:
    schema = load_schema(schema_path)
    manifest = package_release(
        output_dir=output_dir,
        schema=schema,
        training_data_path=training_data_path,
        validation_report_path=validation_report_path if validation_report_path.exists() else None,
    )
    console.print(f"[green]Packaging complete[/green]: {manifest}")


@app.command("all")
def all_cmd(
    source_path: Path,
    oc_version: str,
    artifacts_dir: Path = Path("artifacts"),
    dry_run: bool = True,
) -> None:
    schema_path = artifacts_dir / "schema.json"
    data_path = artifacts_dir / "training_data.jsonl"
    report_path = artifacts_dir / "validation_report.json"

    extract_schema_cmd(source_path=source_path, output=schema_path, oc_version=oc_version)
    generate_training_cmd(schema_path=schema_path, output=data_path)
    fine_tune_cmd(dataset_path=data_path, output_dir=artifacts_dir / "model", dry_run=dry_run)
    validate_model_cmd(schema_path=schema_path, training_data_path=data_path, output=report_path)
    package_cmd(
        schema_path=schema_path,
        training_data_path=data_path,
        validation_report_path=report_path,
        output_dir=Path("dist/release"),
    )
    console.print("[bold green]Pipeline completed[/bold green]")

