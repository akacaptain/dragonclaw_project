from dragonclaw.training_data import generate_training_samples


def test_adversarial_rejection_present(schema_doc):
    rows = generate_training_samples(schema_doc)
    adversarial = [r for r in rows if r.category == "adversarial"]
    assert adversarial
    assert "rejection" in adversarial[0].response

