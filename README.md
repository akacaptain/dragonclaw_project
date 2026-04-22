# DragonClaw

DragonClaw is an AI-powered OpenClaw installer/configurator project with a maintainer pipeline for:
- extracting OpenClaw schema
- generating training data
- orchestrating LoRA fine-tuning
- validating model outputs
- packaging release artifacts

## Quickstart

```bash
cd /Users/captain/dragonclaw_project
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

On many Macs there is no `python` command (only `python3`). If `python3` is missing, install Python from [python.org](https://www.python.org/downloads/) or `brew install python`.

## OpenClaw source and `openclaw.schema.json` (recommended)

DragonClaw’s extractor looks for `openclaw.schema.json` (or `schema.json`) at the **root of the OpenClaw source tree** you pass to `extract-schema`. A plain GitHub source zip usually does **not** include that file; the canonical config JSON Schema is produced by the OpenClaw CLI.

From a working install of the **same OpenClaw version** as your checkout, generate the file **into** that source directory, then run the pipeline:

```bash
cd /path/to/openclaw/source
openclaw config schema > openclaw.schema.json
```

After that, `extract-schema` will use the JSON Schema instead of scanning TypeScript heuristically.

## Pipeline Commands

```bash
# Stage-by-stage (use the same path where openclaw.schema.json lives, if generated)
dragonclaw-build extract-schema /path/to/openclaw/source --oc-version 2026.4.12
dragonclaw-build generate-training
dragonclaw-build fine-tune --dry-run
dragonclaw-build validate-model
dragonclaw-build package

# Full dry-run pipeline
dragonclaw-build all /path/to/openclaw/source 2026.4.12 --dry-run
```

Artifacts are written to `artifacts/` and packaged output to `dist/release/`.

## Notes

- Fine-tuning execution is disabled by default (`--dry-run`) to keep local dev fast and safe. Run real training with **`--no-dry-run`**.
- Real training requires `.[train]` dependencies and GPU-ready environment setup.

## Hugging Face releases (adapters + tokenizer)

If you publish a LoRA adapter to Hugging Face, see `docs/huggingface_release.md` for a practical upload checklist and a `pip list --format=freeze` workflow.
