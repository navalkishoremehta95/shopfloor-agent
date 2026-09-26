"""Replay labeled session events against an SOP."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import ShopContext, Step, WorkOrder, can_start, complete_step


@dataclass
class SessionEvent:
    t: float
    step: str
    hands_clear: bool = True


@dataclass
class Finding:
    t: float
    step: str
    reasons: list[str]


def load_session(path: str | Path) -> list[SessionEvent]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    events: list[SessionEvent] = []
    for item in raw.get("events", []):
        events.append(
            SessionEvent(
                t=float(item["t"]),
                step=str(item["step"]),
                hands_clear=bool(item.get("hands_clear", True)),
            )
        )
    return events


def replay(
    steps: dict[str, Step],
    events: list[SessionEvent],
    order_id: str = "WO-replay",
) -> list[Finding]:
    """Walk events in order. Record violations; only complete legal starts."""
    order = WorkOrder(id=order_id)
    findings: list[Finding] = []

    for ev in events:
        if ev.step not in steps:
            findings.append(
                Finding(t=ev.t, step=ev.step, reasons=[f"unknown step: {ev.step}"])
            )
            continue

        ctx = ShopContext(hands_clear=ev.hands_clear)
        ok, reasons = can_start(steps[ev.step], order, ctx)
        if not ok:
            findings.append(Finding(t=ev.t, step=ev.step, reasons=reasons))
            continue

        complete_step(order, steps[ev.step], ctx)

    return findings


def findings_as_dicts(findings: list[Finding]) -> list[dict[str, Any]]:
    return [
        {"t": f.t, "step": f.step, "reasons": f.reasons} for f in findings
    ]
