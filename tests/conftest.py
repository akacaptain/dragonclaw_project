from pathlib import Path

import pytest

from dragonclaw.io_utils import load_schema, save_schema, save_training_data
from dragonclaw.schema_extractor import extract_schema
from dragonclaw.training_data import generate_training_samples


@pytest.fixture()
def fixture_source_dir(tmp_path: Path) -> Path:
    src = tmp_path / "openclaw-src"
    src.mkdir(parents=True, exist_ok=True)
    fixture = Path(__file__).parent / "fixtures" / "openclaw.schema.json"
    (src / "openclaw.schema.json").write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
    return src


@pytest.fixture()
def schema_doc(fixture_source_dir: Path):
    return extract_schema(fixture_source_dir, oc_version="2026.4.12")


@pytest.fixture()
def schema_path(tmp_path: Path, schema_doc):
    path = tmp_path / "schema.json"
    save_schema(schema_doc, path)
    return path


@pytest.fixture()
def training_path(tmp_path: Path, schema_doc):
    path = tmp_path / "training_data.jsonl"
    save_training_data(generate_training_samples(schema_doc), path)
    return path


@pytest.fixture()
def loaded_schema(schema_path: Path):
    return load_schema(schema_path)

