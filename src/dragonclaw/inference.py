"""Inference interface placeholder for future model runtime integration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InferenceResult:
    text: str


class InferenceEngine:
    def generate(self, prompt: str) -> InferenceResult:
        return InferenceResult(text=f"[mock-response] {prompt}")

