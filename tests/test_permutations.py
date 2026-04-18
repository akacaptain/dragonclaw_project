from dragonclaw.training_data import generate_training_samples


def test_permutation_rows_exist(schema_doc):
    samples = generate_training_samples(schema_doc, seed=123)
    prompts = [s.prompt for s in samples]
    assert any("Configure anthropic with telegram" in p for p in prompts)
    assert any("Configure groq with telegram" in p for p in prompts)

