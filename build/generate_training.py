from pathlib import Path

import typer

from dragonclaw.io_utils import load_schema, save_training_data
from dragonclaw.training_data import generate_training_samples

app = typer.Typer()


@app.command()
def main(
    schema_path: Path = Path("artifacts/schema.json"),
    output: Path = Path("artifacts/training_data.jsonl"),
    seed: int = 42,
) -> None:
    schema = load_schema(schema_path)
    samples = generate_training_samples(schema, seed=seed)
    save_training_data(samples, output)
    typer.echo(f"Wrote {len(samples)} samples to {output}")


if __name__ == "__main__":
    app()
