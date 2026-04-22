# Hugging Face release notes (adapters + tokenizer)

This project fine-tunes a **PEFT/LoRA adapter** on top of a **base model** (see `TrainConfig.base_model` in `src/dragonclaw/models.py`).

When you upload `akacaptain/dragonclaw_model` to the Hub, you generally want the repo to contain:

- **Adapter weights**: `adapter_model.safetensors` (and friends)
- **PEFT config**: `adapter_config.json`
- **Tokenizer files** that match the base model (recommended): `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`, and any companion files your tokenizer save produced

## Why you might see tokenizer errors

If `tokenizer_config.json` contains an invalid value like:

- `"tokenizer_class": "TokenizersBackend"`

then `AutoTokenizer.from_pretrained("<your-adapter-repo>")` can fail, because Transformers does not know that class.

A reliable fix is to **re-save the tokenizer from the same base model you trained on**, then upload those files to the adapter repo.

## Option A: Re-upload a correct tokenizer to the adapter repo

Prerequisites:

- You are logged in (`huggingface-cli login`) and your account has been granted access to **gated** models you load (for example Meta Llama checkpoints).

Run:

```bash
python - <<'PY'
from transformers import AutoTokenizer
from huggingface_hub import HfApi

base_model = "meta-llama/Llama-3.2-3B-Instruct"  # must match adapter_config.json
adapter_repo = "akacaptain/dragonclaw_model"     # your adapter repo id

tok = AutoTokenizer.from_pretrained(base_model)
# Writes tokenizer files into a local folder
out_dir = "hf_tokenizer_export"
tok.save_pretrained(out_dir)

api = HfApi()
# Uploads tokenizer-related files to the adapter repo (repo root)
api.upload_folder(
    folder_path=out_dir,
    repo_id=adapter_repo,
    repo_type="model",
    path_in_repo="",
)
print("Uploaded tokenizer files to", adapter_repo)
PY
```

Cleanup (optional but recommended):

```bash
rm -rf hf_tokenizer_export
```

`hf_tokenizer_export/` is a local throwaway folder; it is listed in `.gitignore` so it is less likely to be committed accidentally.

Sanity check (should work after the upload):

```python
from transformers import AutoTokenizer
AutoTokenizer.from_pretrained("akacaptain/dragonclaw_model")
```

## Reproducibility: `pip freeze` vs “real” dependency locking

**When to document:** as soon as you have *one* working environment for a role (for example “Mac CPU inference” vs “Linux GPU training”). You can always add a second snapshot later; the important part is capturing *what actually worked*.

**Best simple snapshot (recommended for this repo today):**

```bash
python -V > docs/locks/python.txt
python -m pip list --format=freeze > docs/locks/pip-freeze.macos.txt
```

Notes:

- Name the file to include **OS + Python version** (training and inference are often different machines, so keep separate snapshots).
- `pip freeze` is a blunt instrument, but it is the fastest way to prevent “works on my laptop” issues while you are still iterating.
- Do not paste secrets into the repo. Tokens belong in the Hugging Face CLI login / environment variables, not in git.
