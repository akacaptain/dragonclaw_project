"""IO helpers for json and jsonl artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from dragonclaw.models import SchemaDocument, TrainingSample, ValidationReport


def save_schema(schema: SchemaDocument, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(schema.model_dump_json(indent=2), encoding="utf-8")


def load_schema(path: Path) -> SchemaDocument:
    return SchemaDocument.model_validate_json(path.read_text(encoding="utf-8"))


def save_training_data(samples: Iterable[TrainingSample], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for sample in samples:
            handle.write(json.dumps(sample.model_dump(), ensure_ascii=True) + "\n")


def load_training_data(path: Path) -> list[TrainingSample]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(TrainingSample.model_validate_json(line))
    return rows


def save_validation_report(report: ValidationReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

