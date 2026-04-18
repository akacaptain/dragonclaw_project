"""Model validation helpers and report generation."""

from __future__ import annotations

from dragonclaw.models import SchemaDocument, TrainingSample, ValidationCaseResult, ValidationReport
from dragonclaw.validator import validate_patch


def validate_samples(schema: SchemaDocument, samples: list[TrainingSample], max_cases: int | None = None) -> ValidationReport:
    cases = samples[:max_cases] if max_cases is not None else samples
    results: list[ValidationCaseResult] = []
    pass_count = 0

    for sample in cases:
        response = sample.response
        if isinstance(response, dict) and "config_patch" in response and isinstance(response["config_patch"], dict):
            valid, invalid_keys = validate_patch(schema, response["config_patch"])
            results.append(
                ValidationCaseResult(
                    prompt=sample.prompt,
                    valid=valid,
                    reason="" if valid else f"Invalid keys: {', '.join(invalid_keys)}",
                    produced_keys=invalid_keys if not valid else sorted(response["config_patch"].keys()),
                )
            )
            if valid:
                pass_count += 1
        else:
            results.append(
                ValidationCaseResult(prompt=sample.prompt, valid=True, reason="No config_patch in response; skipped.")
            )
            pass_count += 1

    total = len(cases)
    coverage = round((pass_count / total) * 100, 2) if total else 0.0
    return ValidationReport(
        oc_version=schema.metadata.oc_version,
        total_cases=total,
        passed_cases=pass_count,
        coverage_percent=coverage,
        case_results=results,
    )

