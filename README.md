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

## User runtime (chat-first)

For end users, the runtime flow is:

```bash
# from your OpenClaw workspace
dragonclaw --no-dry-run
```

This starts an interactive chat session. Tell DragonClaw what you want changed; it validates and applies config updates.
DragonClaw auto-detects the workspace from the current directory (walking up parent directories). If detection fails, it prompts for a workspace path.

Session context is persisted per workspace and session id (default: `default`), so follow-up turns can inherit context like the last target file.

```bash
dragonclaw --session-id my-session --no-dry-run
```

Developer-only helper commands still exist under `dragonclaw` for debugging, but they are intentionally hidden from primary UX docs.

## Developer notes: applying complete OpenClaw config files

1. Extract schema and discover config file references from OpenClaw source:

```bash
dragonclaw-build extract-schema /path/to/openclaw/source --oc-version 2026.4.12
```

2. Create `artifacts/config_plan.json` with file-relative JSON patches:

```json
{
  "openclaw.json": {
    "provider": "openai"
  },
  "auth/profiles/default.json": {
    "name": "default",
    "token": "replace-me"
  }
}
```

3. Preview and apply:

```bash
dragonclaw apply-config /path/to/openclaw/workspace --dry-run
dragonclaw apply-config /path/to/openclaw/workspace --no-dry-run
```

`apply-config` merges with existing JSON objects and writes `.bak` files before overwriting by default.

4. Verify discovered surface against a real workspace:

```bash
dragonclaw verify-config-surface /path/to/openclaw/workspace
```

This reports expected files present, missing expected files, and extra JSON files in the workspace.

For CI-style gating, use:

```bash
dragonclaw verify-config-surface /path/to/openclaw/workspace --fail-on-missing --fail-on-extra
```

## Notes

- Fine-tuning execution is disabled by default (`--dry-run`) to keep local dev fast and safe. Run real training with **`--no-dry-run`**.
- Real training requires `.[train]` dependencies and GPU-ready environment setup.

## Hugging Face releases (adapters + tokenizer)

If you publish a LoRA adapter to Hugging Face, see `docs/huggingface_release.md` for a practical upload checklist and a `pip list --format=freeze` workflow.

A ready-to-copy model card template lives in `docs/huggingface_model_card.md`.
