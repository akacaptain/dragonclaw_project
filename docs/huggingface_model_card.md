---
license: llama3.2
language:
  - en
base_model: meta-llama/Llama-3.2-3B-Instruct
tags:
  - llama
  - lora
  - peft
  - text-generation
  - openclaw
---

# akacaptain/dragonclaw_model

## Model summary

`akacaptain/dragonclaw_model` is a **LoRA (PEFT) adapter** fine-tuned on top of Meta’s `meta-llama/Llama-3.2-3B-Instruct`.

It is **not** a standalone full model checkpoint: you must load the **base** `Llama-3.2-3B-Instruct` model and then apply this adapter.

## How to use (Transformers)

Prereqs:

- You must be granted access to the gated base model on Hugging Face and be logged in (`huggingface-cli login`).

Load:

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

base_model = "meta-llama/Llama-3.2-3B-Instruct"
adapter_repo = "akacaptain/dragonclaw_model"

tok = AutoTokenizer.from_pretrained(adapter_repo)
base = AutoModelForCausalLM.from_pretrained(base_model)
model = PeftModel.from_pretrained(base, adapter_repo)
model.eval()

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"},
]
prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tok(prompt, return_tensors="pt")

with torch.inference_mode():
    out = model.generate(
        **inputs,
        max_new_tokens=128,
        do_sample=False,
        pad_token_id=tok.eos_token_id,
    )

print(tok.decode(out[0], skip_special_tokens=True))
```

## Training details

- **Base model**: `meta-llama/Llama-3.2-3B-Instruct`
- **Method**: LoRA / PEFT (see `adapter_config.json`)
- **Training hardware**: NVIDIA RTX 4090
- **Approximate training duration**: ~10 minutes
- **Data**: Fine-tuned on synthetically generated training data derived from the OpenClaw source code.

## Evaluation

- **Automated evaluation**: TODO (or: not yet published)

## Limitations

- Inherits the limitations and usage constraints of the base `Llama-3.2-3B-Instruct` model.
- Synthetic training data can produce confident-sounding but incorrect configuration advice; always verify in real environments.

## License / attribution

- Ensure your Hub license/settings match the **base model** requirements and your organization’s policy.
