# DragonClaw — AI-Powered OpenClaw Installer & Configurator

## Vision
A single tool that installs, configures, and troubleshoots OpenClaw through natural language conversation. No more fighting with JSON config files, hallucinating LLMs, or broken setup wizards. You tell it what you want, it does it correctly — every time.

Free and open source. Built by and for the OpenClaw community.

---

## Problem
OpenClaw's current setup experience is broken:
- The config wizard doesn't cover most providers (Groq, OpenRouter, etc.)
- The `openclaw.json` schema is undocumented and changes between versions
- LLMs (Claude, Gemini, ChatGPT) hallucinate config keys when asked for help
- Setting up non-default providers requires manually editing JSON with trial and error
- Error messages reference config keys but don't tell you the valid values
- Users routinely spend hours or days debugging configuration

## Solution
A fine-tuned small language model that knows the OpenClaw config schema perfectly because it was trained on the actual source code. It cannot hallucinate config keys because it has been validated against every permutation. It runs locally, in the terminal, and speaks plain English.

---

## Architecture Overview

The project has three components:

```
┌─────────────────────────────────────────────────┐
│                 BUILD PIPELINE                   │
│                                                  │
│  OC Release ─→ Schema Extractor ─→ Training     │
│                    │                Data Gen     │
│                    │                  │          │
│                    ▼                  ▼          │
│              Validation          Fine-tune      │
│               Layer              Llama 3.2 3B   │
│                    │                  │          │
│                    ▼                  ▼          │
│              Test Suite ◄──── Trained Model      │
│                    │                             │
│                    ▼                             │
│             Packaged Installer                   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│                THE INSTALLER                     │
│            (what users download)                 │
│                                                  │
│  Fine-tuned Model + Schema Validator + CLI Chat  │
│                                                  │
│  Capabilities:                                   │
│  - Install OpenClaw from scratch                 │
│  - Configure new installations                   │
│  - Update existing configurations                │
│  - Diagnose config-related errors                │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│                 TEST SUITE                       │
│                                                  │
│  Every valid config permutation tested           │
│  Model output validated against extracted schema │
│  Regression tests on each rebuild                │
└─────────────────────────────────────────────────┘
```

---

## 1. Build Pipeline

### Purpose
Takes an OpenClaw release as input and produces a packaged installer with a fine-tuned model. This is what the maintainer (you) runs when a new OC version drops. It is NOT what end users run.

### Inputs
- OpenClaw source code (specific release tag/version)
- Base model: Llama 3.2 3B

### Pipeline Steps

#### Step 1: Schema Extraction
- Parse the OpenClaw source code to find config schema definitions (likely Zod schemas in TypeScript)
- Extract every valid config key, its type, allowed values, defaults, and constraints
- Extract all valid model/provider identifiers and their required fields
- Extract all valid channel configs (Telegram, Discord, iMessage)
- Extract all valid tool configs
- Extract all valid hook configs
- Output: `schema.json` — a complete, machine-readable representation of every valid config structure

#### Step 2: Training Data Generation
From `schema.json`, programmatically generate Q&A pairs:

**Installation pairs:**
```
Q: "Install OpenClaw"
A: { "action": "install", "steps": [...] }

Q: "I don't have Node.js installed"
A: { "action": "install_dependency", "dependency": "node", "steps": [...] }
```

**Configuration pairs (hundreds/thousands):**
```
Q: "Set up Groq with Llama 3.3 70B as my primary model"
A: { "config_patch": { ... valid JSON ... } }

Q: "Configure Telegram with bot token ABC123"
A: { "config_patch": { ... valid JSON ... } }

Q: "Add OpenRouter as a fallback provider"
A: { "config_patch": { ... valid JSON ... } }

Q: "Set heartbeat interval to 5 hours with isolated sessions"
A: { "config_patch": { ... valid JSON ... } }
```

**Error diagnosis pairs:**
```
Q: "I'm getting: Config invalid - tools.elevated.allowFrom.telegram: Invalid input: expected array, received boolean"
A: { "diagnosis": "...", "config_patch": { ... fix ... } }

Q: "401 Missing Authentication header when using OpenRouter"
A: { "diagnosis": "...", "config_patch": { ... fix ... } }
```

**Multi-turn conversation pairs:**
```
Q: "I want to set up my agent"
A: "What model provider do you want to use? (Anthropic, OpenAI, Groq, OpenRouter, or a custom provider)"
Q: "Groq"
A: "Which model? Options for Groq include: llama-3.3-70b-versatile, llama-3.1-8b-instant, ..."
Q: "llama-3.3-70b"
A: "Do you have a Groq API key? You can get one at console.groq.com/keys"
Q: "yes, it's gsk_abc123"
A: { "config_patch": { ... complete valid config ... } }
```

**Permutation coverage:**
- Every supported provider × every supported model
- Every channel type × every config option
- Every tool × every valid setting
- Common multi-provider setups (primary + fallbacks)
- Every error message in the OC source → diagnosis + fix

Output: `training_data.jsonl`

#### Step 3: Fine-tuning
- Base model: Llama 3.2 3B (via Hugging Face / Unsloth / LoRA)
- Training data: `training_data.jsonl`
- Fine-tuning approach: LoRA (Low-Rank Adaptation) for efficiency
- Output: Fine-tuned model weights (adapter or merged)

#### Step 4: Validation
- Run every generated Q&A pair through the fine-tuned model
- Validate every config output against `schema.json`
- Any invalid config output = test failure
- Generate a coverage report: % of schema covered, % of permutations passing

#### Step 5: Packaging
- Bundle the fine-tuned model, schema validator, and CLI interface
- Package for distribution via pip
- Tag with the supported OpenClaw version(s)

---

## 2. The Installer (User-Facing Tool)

### Installation
```bash
pip install dragonclaw
```

### Usage
```bash
# Fresh install — installs and configures OpenClaw
dragonclaw

# Configure existing installation
dragonclaw config

# Diagnose a config error
dragonclaw fix

# Specify target OC version
dragonclaw --oc-version 2026.3.28
```

### Chat Interface
On launch, the tool drops into an interactive chat:

```
🦞 DragonClaw v1.0 — AI-powered OpenClaw installer
   Supports OpenClaw 2026.3.28 - 2026.4.12

What would you like to do?
- Install OpenClaw (fresh install)
- Configure an existing installation
- Fix a config error

> I want to install OpenClaw and set it up with Groq using Llama 3.3

Checking prerequisites...
✓ Node.js v22.22.0 found
✓ npm available

Installing OpenClaw...
✓ OpenClaw 2026.4.12 installed

Now let's configure it.

Which Groq model do you want as your primary?
1. llama-3.3-70b-versatile (recommended for agentic tasks)
2. llama-3.1-70b-versatile
3. llama-3.1-8b-instant (fastest, least capable)

> 1

Do you have a Groq API key? Get one at console.groq.com/keys

> yes, gsk_abc123...

Do you want to set up any channels? (Telegram, Discord, or none for now)

> Telegram

I'll need your Telegram bot token from @BotFather.

> 8762718470:AAF...

Generating config...
Validating against OpenClaw 2026.4.12 schema...
✓ Config valid

Here's what I'll write to ~/.openclaw/openclaw.json:
[shows diff or summary of key settings]

Apply this config? (y/n)

> y

✓ Config written
✓ Auth profile created

You're ready to go! Run `openclaw gateway` to start.
```

### Core Capabilities

#### Fresh Installation
1. Check for Node.js — install if missing (via nvm or direct)
2. Install OpenClaw via the correct install command for the supported version
3. Run initial setup
4. Drop into config chat

#### Configuration (new or existing)
1. Read existing `openclaw.json` if present
2. Chat with user about what they want
3. Generate config changes
4. Validate ALL output against extracted schema before writing — NEVER write invalid config
5. Show changes to user for approval
6. Write config and create any necessary auth profiles
7. Optionally restart gateway if running

#### Error Diagnosis
1. User pastes error message or describes problem
2. Model identifies the config key and constraint that's failing
3. Generates the fix
4. Validates fix against schema
5. Applies with user approval

### Validation Layer (Critical)
Every config output from the model passes through a hard validation layer before being shown to the user or written to disk. This is NOT optional. The validator uses the same schema extracted from the OC source code.

```
Model generates config → Validator checks against schema.json
                              │
                         ┌────┴────┐
                         │         │
                       VALID    INVALID
                         │         │
                    Show to     Retry with
                     user      error context
                               (max 3 retries,
                                then surface
                                error to user)
```

If the model generates invalid config 3 times in a row, it tells the user honestly: "I'm not confident I can generate a valid config for this. Here's what I tried and why it failed. You may need to configure this manually."

---

## 3. Test Suite

### Purpose
Ensure the fine-tuned model never generates invalid configs. Run on every rebuild.

### Test Categories

#### Schema Coverage Tests
- For every key in `schema.json`, generate a prompt that should produce a config using that key
- Validate the output includes the key with a valid value
- Target: 100% key coverage

#### Permutation Tests
- Every provider × model combination
- Every channel × config option combination
- Every tool × setting combination
- Validate all outputs against schema

#### Error Diagnosis Tests
- Feed every known OC error message pattern
- Validate that the proposed fix is valid config
- Validate that the fix addresses the specific error

#### Regression Tests
- A fixed set of common user scenarios that must always pass:
  - "Set up Anthropic with Sonnet as primary"
  - "Configure Groq with Llama 3.3"
  - "Add Telegram channel"
  - "Set heartbeat to 3 hours with isolated sessions"
  - "Add OpenRouter with auto model"
  - "Fix: Config invalid — expected array, received boolean"
  - etc.

#### Adversarial Tests
- Prompts designed to trick the model into generating invalid config
- Prompts with fake config keys to test if the model rejects them
- Prompts asking for features that don't exist in the supported OC version

### Test Output
```
DragonClaw Test Suite — OC 2026.4.12
================================
Schema coverage:  347/347 keys (100%)
Permutation tests: 2,841/2,841 passed
Error diagnosis:   89/89 passed
Regression tests:  45/45 passed
Adversarial tests: 30/30 passed

✓ All tests passed. Model ready for packaging.
```

---

## Tech Stack

- **Language:** Python 3.10+
- **CLI Framework:** Rich (for terminal UI) + Prompt Toolkit (for chat input)
- **Model:** Llama 3.2 3B, fine-tuned with LoRA
- **Fine-tuning:** Unsloth or Hugging Face PEFT
- **Inference:** llama.cpp (via llama-cpp-python) for local inference
- **Schema parsing:** Tree-sitter (for parsing TypeScript/Zod schemas from OC source)
- **Validation:** JSON Schema or custom validator generated from extracted schema
- **Testing:** pytest
- **Distribution:** PyPI (pip install dragonclaw)
- **License:** MIT

---

## Supported OpenClaw Versions (v1)
- Start with one well-tested version (e.g., 2026.3.28 or 2026.4.12)
- Each supported version gets its own fine-tuned model and schema
- The installer auto-detects installed OC version and loads the correct model
- Users can specify version with `--oc-version`

---

## What's In (v1)
- Fresh OpenClaw installation
- Full config generation via chat
- All major providers: Anthropic, OpenAI, Groq, OpenRouter, custom providers
- All channels: Telegram, Discord
- Heartbeat, session, compaction config
- Tool configuration
- Auth profile management
- Config error diagnosis and fixing
- Schema validation on every output
- Comprehensive test suite

## What's Out (v1)
- Gateway management (start/stop/monitoring)
- Runtime debugging (non-config errors)
- Skill/plugin installation
- Multi-agent configuration
- Cron job setup
- Custom hook configuration
- Auto-updating when new OC versions drop (manual rebuild for now)

---

## Project Structure
```
dragonclaw/
├── README.md
├── pyproject.toml
├── src/
│   └── dragonclaw/
│       ├── __init__.py
│       ├── cli.py              # Entry point, chat interface
│       ├── installer.py        # OC installation logic
│       ├── configurator.py     # Config generation + writing
│       ├── validator.py        # Schema validation layer
│       ├── diagnostics.py      # Error diagnosis
│       ├── inference.py        # Model loading + inference
│       └── schema/
│           └── schema.json     # Extracted schema (bundled)
├── build/
│   ├── extract_schema.py       # Parses OC source → schema.json
│   ├── generate_training.py    # schema.json → training_data.jsonl
│   ├── fine_tune.py            # Runs the LoRA fine-tune
│   ├── validate_model.py       # Post-training validation
│   └── package.py              # Bundles everything for distribution
├── tests/
│   ├── test_schema_coverage.py
│   ├── test_permutations.py
│   ├── test_error_diagnosis.py
│   ├── test_regression.py
│   └── test_adversarial.py
└── models/
    └── (fine-tuned model weights, not checked into git)
```

---

## Distribution Strategy
- Open source on GitHub (MIT license)
- Published to PyPI as `dragonclaw`
- Announce on OpenClaw Discord, Reddit, X
- Model weights hosted on Hugging Face
- Listed on OpenMart as a free product (drives traffic to the marketplace)

---

## Open Questions
1. **Model hosting:** Download on first run from Hugging Face. The pip package stays small and fast to install. On first launch, DragonClaw downloads the fine-tuned model (~2-6GB depending on quantization) with a progress bar and caches it locally at `~/.dragonclaw/models/`. Subsequent runs use the cached model.
2. **OC source access:** Is the OpenClaw source code on GitHub publicly accessible, or will schema extraction require a local installation?
3. **Auth profile format:** The `auth-profiles.json` file format needs to be extracted alongside the config schema — it's a separate file with its own structure
4. **~~Naming:~~** DragonClaw ✓
