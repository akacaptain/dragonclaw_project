"""Fine-tune orchestration for LoRA training."""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dragonclaw.io_utils import load_training_data
from dragonclaw.models import TrainConfig, TrainingSample

if TYPE_CHECKING:
    from transformers import PreTrainedTokenizerBase


class FineTuneBackend:
    name = "base"

    def check_environment(self) -> list[str]:
        return []

    def run(self, config: TrainConfig) -> str:
        raise NotImplementedError


def _response_text(sample: TrainingSample) -> str:
    if isinstance(sample.response, str):
        return sample.response
    return json.dumps(sample.response, ensure_ascii=False)


def _encode_chat_example(
    tokenizer: PreTrainedTokenizerBase,
    prompt: str,
    response_text: str,
    max_length: int,
) -> dict[str, list[int]]:
    if getattr(tokenizer, "chat_template", None) is None:
        raise ValueError(
            "Tokenizer has no chat_template; use an Instruct/chat checkpoint "
            "(e.g. meta-llama/Llama-3.2-3B-Instruct)."
        )
    messages = [
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": response_text},
    ]
    full_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )
    prefix_text = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize=False,
        add_generation_prompt=True,
    )
    full_ids = tokenizer(
        full_text,
        max_length=max_length,
        truncation=True,
        add_special_tokens=False,
    )["input_ids"]
    prefix_ids = tokenizer(prefix_text, add_special_tokens=False, truncation=False)["input_ids"]
    prefix_len = min(len(prefix_ids), len(full_ids))
    if prefix_len and full_ids[:prefix_len] != prefix_ids[:prefix_len]:
        prefix_len = 0
    labels = list(full_ids)
    for i in range(prefix_len):
        labels[i] = -100
    return {"input_ids": full_ids, "labels": labels}


def _run_hf_peft_training(config: TrainConfig) -> str:
    import torch
    from datasets import Dataset
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
    )

    samples = load_training_data(Path(config.dataset_path))
    if not samples:
        raise ValueError("Training dataset is empty.")

    out = Path(config.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "train_config.json").write_text(config.model_dump_json(indent=2), encoding="utf-8")

    tokenizer = AutoTokenizer.from_pretrained(config.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    rows = [
        _encode_chat_example(tokenizer, s.prompt, _response_text(s), config.max_seq_length)
        for s in samples
    ]
    ds = Dataset.from_list(rows)

    torch_dtype = (
        torch.bfloat16
        if torch.cuda.is_available() and torch.cuda.is_bf16_supported()
        else (torch.float16 if torch.cuda.is_available() else torch.float32)
    )
    load_kw: dict[str, Any] = {
        "torch_dtype": torch_dtype,
        "trust_remote_code": True,
    }
    if importlib.util.find_spec("accelerate") is not None and torch.cuda.is_available():
        load_kw["device_map"] = "auto"
    model = AutoModelForCausalLM.from_pretrained(config.base_model, **load_kw)
    if load_kw.get("device_map") is None and torch.cuda.is_available():
        model = model.cuda()

    lora = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    )
    model = get_peft_model(model, lora)
    model.enable_input_require_grads()

    @dataclass
    class _CausalCollator:
        tokenizer: Any

        def __call__(self, features: list[dict[str, Any]]) -> dict[str, torch.Tensor]:
            pad_id = self.tokenizer.pad_token_id
            if pad_id is None:
                raise ValueError("Tokenizer.pad_token_id must be set for batching.")
            max_len = max(len(f["input_ids"]) for f in features)
            batch_input: list[list[int]] = []
            batch_labels: list[list[int]] = []
            attn: list[list[int]] = []
            for f in features:
                ids = f["input_ids"]
                lab = f["labels"]
                pad_len = max_len - len(ids)
                batch_input.append(ids + [pad_id] * pad_len)
                batch_labels.append(lab + [-100] * pad_len)
                attn.append([1] * len(ids) + [0] * pad_len)
            return {
                "input_ids": torch.tensor(batch_input, dtype=torch.long),
                "labels": torch.tensor(batch_labels, dtype=torch.long),
                "attention_mask": torch.tensor(attn, dtype=torch.long),
            }

    use_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    use_fp16 = torch.cuda.is_available() and not use_bf16
    args = TrainingArguments(
        output_dir=str(out),
        num_train_epochs=config.num_train_epochs,
        per_device_train_batch_size=config.per_device_train_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        warmup_ratio=config.warmup_ratio,
        logging_steps=config.logging_steps,
        save_steps=config.save_steps,
        save_total_limit=2,
        bf16=use_bf16,
        fp16=use_fp16,
        gradient_checkpointing=True,
        optim="adamw_torch",
        report_to="none",
        seed=config.seed,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=ds,
        data_collator=_CausalCollator(tokenizer),
    )
    trainer.train()
    trainer.save_model(str(out))
    tokenizer.save_pretrained(str(out))
    return f"Training finished. LoRA adapter and tokenizer saved under {out}"


class HfPeftBackend(FineTuneBackend):
    name = "hf-peft"

    def check_environment(self) -> list[str]:
        missing = []
        for dep in ("transformers", "datasets", "peft", "torch"):
            if importlib.util.find_spec(dep) is None:
                missing.append(dep)
        return missing

    def run(self, config: TrainConfig) -> str:
        return _run_hf_peft_training(config)


class UnslothBackend(FineTuneBackend):
    name = "unsloth"

    def check_environment(self) -> list[str]:
        missing = []
        for dep in ("transformers", "datasets", "peft"):
            if importlib.util.find_spec(dep) is None:
                missing.append(dep)
        return missing

    def run(self, config: TrainConfig) -> str:
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        raise NotImplementedError(
            "Unsloth backend is not implemented yet; use --backend hf-peft for real training."
        )


def get_backend(name: str) -> FineTuneBackend:
    if name == "hf-peft":
        return HfPeftBackend()
    if name == "unsloth":
        return UnslothBackend()
    raise ValueError(f"Unsupported backend: {name}")


def run_fine_tune(config: TrainConfig) -> str:
    dataset = Path(config.dataset_path)
    if not dataset.exists():
        raise FileNotFoundError(f"Training dataset not found: {dataset}")

    backend = get_backend(config.backend)
    if config.dry_run:
        missing = backend.check_environment()
        if missing:
            missing_list = ", ".join(sorted(set(missing)))
            return f"Dry run warning. Missing optional training deps for {backend.name}: {missing_list}"
        return f"Dry run OK. Backend {backend.name} ready for dataset {dataset}."

    missing = backend.check_environment()
    if missing:
        raise RuntimeError(f"Missing training dependencies for {backend.name}: {', '.join(sorted(set(missing)))}")

    return backend.run(config)
