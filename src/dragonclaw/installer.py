"""OpenClaw installation helpers (maintainer-facing placeholder)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InstallPlan:
    oc_version: str
    steps: list[str]


def build_install_plan(oc_version: str) -> InstallPlan:
    return InstallPlan(
        oc_version=oc_version,
        steps=[
            "Check Node.js availability",
            "Install requested OpenClaw version",
            "Run baseline setup",
        ],
    )

