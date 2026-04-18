"""Shared data contracts for all pipeline stages."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class SchemaField(BaseModel):
    key: str
    field_type: str = "unknown"
    required: bool = False
    default: Any = None
    enum_values: list[str] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)


class SchemaMetadata(BaseModel):
    oc_version: str
    extracted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_hash: str
    source_path: str


class SchemaDocument(BaseModel):
    metadata: SchemaMetadata
    fields: list[SchemaField] = Field(default_factory=list)

    def field_map(self) -> dict[str, SchemaField]:
        return {f.key: f for f in self.fields}


class TrainingSample(BaseModel):
    category: Literal["install", "configure", "diagnose", "conversation", "adversarial"]
    prompt: str
    response: dict[str, Any] | str
    tags: list[str] = Field(default_factory=list)


class TrainConfig(BaseModel):
    base_model: str = "meta-llama/Llama-3.2-3B-Instruct"
    dataset_path: str
    output_dir: str
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    backend: Literal["hf-peft", "unsloth"] = "hf-peft"
    dry_run: bool = True


class ValidationCaseResult(BaseModel):
    prompt: str
    valid: bool
    attempts: int = 1
    reason: str = ""
    produced_keys: list[str] = Field(default_factory=list)


class ValidationReport(BaseModel):
    oc_version: str
    total_cases: int
    passed_cases: int
    coverage_percent: float
    case_results: list[ValidationCaseResult] = Field(default_factory=list)

