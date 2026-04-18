from dragonclaw.evaluation import validate_samples
from dragonclaw.training_data import generate_training_samples


def test_regression_like_validation_passes(schema_doc):
    rows = generate_training_samples(schema_doc, seed=42)
    report = validate_samples(schema_doc, rows, max_cases=25)
    assert report.total_cases >= 20
    assert report.passed_cases >= 14

