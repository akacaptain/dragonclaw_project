from pathlib import Path

import typer

from dragonclaw.io_utils import save_schema
from dragonclaw.schema_extractor import extract_schema

app = typer.Typer()


@app.command()
def main(source_path: Path, output: Path = Path("artifacts/schema.json"), oc_version: str = "unknown") -> None:
    schema = extract_schema(source_path, oc_version=oc_version)
    save_schema(schema, output)
    typer.echo(f"Wrote schema to {output}")


if __name__ == "__main__":
    app()
