# Training Environment

## Recommended baseline
- Python 3.10+
- CUDA-capable GPU (for non-dry-run)
- Sufficient disk for model and adapters

## Install dependencies

```bash
pip install -e ".[train,dev]"
```

## Validate environment quickly

```bash
dragonclaw-build fine-tune --dry-run
```

## Run non-dry training

```bash
dragonclaw-build fine-tune --dry-run false --backend hf-peft
```

Use `--backend unsloth` once the unsloth integration package is installed and verified.
