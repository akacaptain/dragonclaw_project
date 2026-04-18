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

## Pipeline Commands

```bash
# Stage-by-stage
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

- Fine-tuning execution is disabled by default (`--dry-run`) to keep local dev fast and safe.
- Real training requires `.[train]` dependencies and GPU-ready environment setup.
