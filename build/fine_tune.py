from pathlib import Path

import typer

from dragonclaw.fine_tune import run_fine_tune
from dragonclaw.models import TrainConfig

app = typer.Typer()


@app.command()
def main(
    dataset_path: Path = Path("artifacts/training_data.jsonl"),
    output_dir: Path = Path("artifacts/model"),
    base_model: str = "meta-llama/Llama-3.2-3B-Instruct",
    backend: str = "hf-peft",
    dry_run: bool = True,
) -> None:
    config = TrainConfig(
        dataset_path=str(dataset_path),
        output_dir=str(output_dir),
        base_model=base_model,
        backend=backend,  # type: ignore[arg-type]
        dry_run=dry_run,
    )
    msg = run_fine_tune(config)
    typer.echo(msg)


if __name__ == "__main__":
    app()
