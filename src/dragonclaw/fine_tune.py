"""Fine-tune orchestration for LoRA training."""

from __future__ import annotations

import importlib
from pathlib import Path

from dragonclaw.models import TrainConfig


class FineTuneBackend:
    name = "base"

    def check_environment(self) -> list[str]:
        return []

    def run(self, config: TrainConfig) -> str:
        raise NotImplementedError


class HfPeftBackend(FineTuneBackend):
    name = "hf-peft"

    def check_environment(self) -> list[str]:
        missing = []
        for dep in ("transformers", "datasets", "peft"):
            if importlib.util.find_spec(dep) is None:
                missing.append(dep)
        return missing

    def run(self, config: TrainConfig) -> str:
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        marker = Path(config.output_dir) / "train_job.json"
        marker.write_text(config.model_dump_json(indent=2), encoding="utf-8")
        return f"Prepared HF PEFT training job in {marker}"


class UnslothBackend(FineTuneBackend):
    name = "unsloth"

    def check_environment(self) -> list[str]:
        missing = []
        for dep in ("transformers", "datasets", "peft"):
            if importlib.util.find_spec(dep) is None:
                missing.append(dep)
        return missing

    def run(self, config: TrainConfig) -> str:
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        marker = Path(config.output_dir) / "unsloth_train_job.json"
        marker.write_text(config.model_dump_json(indent=2), encoding="utf-8")
        return f"Prepared Unsloth training job in {marker}"


def get_backend(name: str) -> FineTuneBackend:
    if name == "hf-peft":
        return HfPeftBackend()
    if name == "unsloth":
        return UnslothBackend()
    raise ValueError(f"Unsupported backend: {name}")


def run_fine_tune(config: TrainConfig) -> str:
    dataset = Path(config.dataset_path)
    if not dataset.exists():
        raise FileNotFoundError(f"Training dataset not found: {dataset}")

    backend = get_backend(config.backend)
    if config.dry_run:
        missing = backend.check_environment()
        if missing:
            missing_list = ", ".join(sorted(set(missing)))
            return f"Dry run warning. Missing optional training deps for {backend.name}: {missing_list}"
        return f"Dry run OK. Backend {backend.name} ready for dataset {dataset}."

    missing = backend.check_environment()
    if missing:
        raise RuntimeError(f"Missing training dependencies for {backend.name}: {', '.join(sorted(set(missing)))}")

    return backend.run(config)

