# Training Environment

## Recommended baseline
- Python 3.10+
- CUDA-capable GPU (for non-dry-run)
- Sufficient disk for model and adapters
- **PyTorch with CUDA** on the GPU machine (install the wheel that matches the host CUDA; `pip install -e ".[train]"` pulls CPU PyTorch in some environments, so you may need a separate `pip install torch` from [pytorch.org](https://pytorch.org/get-started/locally/) first)
- **Hugging Face access** for gated models (e.g. Llama): `huggingface-cli login` or `HF_TOKEN` in the environment

## Install dependencies

```bash
pip install -e ".[train,dev]"
```

## Validate environment quickly

```bash
dragonclaw-build fine-tune --dry-run
```

## Run non-dry training

Typer does not accept `--dry-run false`; use **`--no-dry-run`** to turn dry-run off.

```bash
dragonclaw-build fine-tune --no-dry-run --backend hf-peft
```

Use `--backend unsloth` once the unsloth integration package is installed and verified.
