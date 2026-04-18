from pathlib import Path

import typer

from dragonclaw.evaluation import validate_samples
from dragonclaw.io_utils import load_schema, load_training_data, save_validation_report

app = typer.Typer()


@app.command()
def main(
    schema_path: Path = Path("artifacts/schema.json"),
    training_data_path: Path = Path("artifacts/training_data.jsonl"),
    output: Path = Path("artifacts/validation_report.json"),
    max_cases: int | None = None,
) -> None:
    schema = load_schema(schema_path)
    rows = load_training_data(training_data_path)
    report = validate_samples(schema, rows, max_cases=max_cases)
    save_validation_report(report, output)
    typer.echo(f"Wrote validation report to {output}")


if __name__ == "__main__":
    app()
