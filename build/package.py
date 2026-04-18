from pathlib import Path

import typer

from dragonclaw.io_utils import load_schema
from dragonclaw.packaging import package_release

app = typer.Typer()


@app.command()
def main(
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
    typer.echo(f"Wrote release manifest to {manifest}")


if __name__ == "__main__":
    app()
