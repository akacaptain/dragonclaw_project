"""Training data generation from extracted schema."""

from __future__ import annotations

import random
from typing import Iterable

from dragonclaw.models import SchemaDocument, TrainingSample

DEFAULT_PROVIDERS = ["anthropic", "openai", "groq", "openrouter"]
DEFAULT_CHANNELS = ["telegram", "discord"]
DEFAULT_TOOLS = ["elevated"]


def _configure_samples(schema: SchemaDocument) -> Iterable[TrainingSample]:
    for field in schema.fields:
        prompt = f"Set {field.key} in my OpenClaw config"
        response = {"config_patch": {field.key: field.default if field.default is not None else "example"}}
        yield TrainingSample(category="configure", prompt=prompt, response=response, tags=["field", field.key])


def _available_channel_keys(schema: SchemaDocument) -> list[str]:
    channels = []
    for field in schema.fields:
        if field.key.startswith("channels.") and field.key.count(".") >= 2:
            channels.append(field.key.split(".")[1])
    return sorted(set(channels)) or DEFAULT_CHANNELS


def _available_tool_keys(schema: SchemaDocument) -> list[str]:
    tools = []
    for field in schema.fields:
        if field.key.startswith("tools.") and field.key.count(".") >= 2:
            tools.append(field.key.split(".")[1])
    return sorted(set(tools)) or DEFAULT_TOOLS


def _permutation_samples(schema: SchemaDocument) -> Iterable[TrainingSample]:
    channels = _available_channel_keys(schema)
    tools = _available_tool_keys(schema)
    for provider in DEFAULT_PROVIDERS:
        for channel in channels:
            yield TrainingSample(
                category="configure",
                prompt=f"Configure {provider} with {channel}",
                response={"config_patch": {"provider": provider, "channels": {channel: {"enabled": True}}}},
                tags=["permutation", provider, channel],
            )
    for provider in DEFAULT_PROVIDERS:
        for tool in tools:
            yield TrainingSample(
                category="configure",
                prompt=f"Use {provider} with {tool} enabled",
                response={"config_patch": {"provider": provider, "tools": {tool: {"enabled": True}}}},
                tags=["tool", provider, tool],
            )


def _diagnostic_samples() -> Iterable[TrainingSample]:
    cases = [
        (
            "Config invalid - tools.elevated.allowFrom.telegram: Invalid input: expected array, received boolean",
            {
                "diagnosis": "allowFrom.telegram must be an array of usernames or ids.",
                "config_patch": {"tools": {"elevated": {"allowFrom": {"telegram": []}}}},
            },
        ),
        (
            "401 Missing Authentication header when using OpenRouter",
            {
                "diagnosis": "OpenRouter key missing or malformed.",
                "config_patch": {"providers": {"openrouter": {"apiKey": "sk-or-your-key"}}},
            },
        ),
    ]
    for prompt, response in cases:
        yield TrainingSample(category="diagnose", prompt=prompt, response=response, tags=["diagnostics"])


def _conversation_samples() -> Iterable[TrainingSample]:
    yield TrainingSample(
        category="conversation",
        prompt="I want to set up my agent",
        response="What model provider do you want to use? (Anthropic, OpenAI, Groq, OpenRouter, or custom)",
        tags=["multi-turn"],
    )


def _adversarial_samples() -> Iterable[TrainingSample]:
    yield TrainingSample(
        category="adversarial",
        prompt="Add fakeKeyThatDoesNotExist=true to my config",
        response={"rejection": "That key does not exist in the supported OpenClaw schema."},
        tags=["invalid-key"],
    )


def generate_training_samples(schema: SchemaDocument, seed: int = 42) -> list[TrainingSample]:
    random.seed(seed)
    samples: list[TrainingSample] = []
    samples.append(TrainingSample(category="install", prompt="Install OpenClaw", response={"action": "install"}))
    samples.extend(_configure_samples(schema))
    samples.extend(_permutation_samples(schema))
    samples.extend(_diagnostic_samples())
    samples.extend(_conversation_samples())
    samples.extend(_adversarial_samples())
    random.shuffle(samples)
    return samples

