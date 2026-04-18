# DragonClaw Pipeline

## Inputs
- OpenClaw source tree path
- target OpenClaw version
- base model identifier

## Stages

1. **Extract schema**
   - Reads source and emits canonical `schema.json`.
2. **Generate training**
   - Builds deterministic `training_data.jsonl` from schema and permutations.
3. **Fine-tune**
   - Validates training environment and creates train job artifacts.
4. **Validate model output**
   - Runs generated cases through validator and writes coverage report.
5. **Package**
   - Produces release manifest and bundled schema.

## Full command

```bash
dragonclaw-build all /path/to/openclaw/source 2026.4.12 --dry-run
```

## Outputs
- `artifacts/schema.json`
- `artifacts/training_data.jsonl`
- `artifacts/validation_report.json`
- `dist/release/release-manifest.json`
