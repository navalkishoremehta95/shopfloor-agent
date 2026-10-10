"""Replay labeled session events against an SOP."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from . import ShopContext, Step, WorkOrder, complete_step
from .decide import Decision, decide
from .map_actions import map_action_to_step


@dataclass
class SessionEvent:
    t: float
    step: str | None = None
    action: str | None = None
    hands_clear: bool = True


@dataclass
class Finding:
    t: float
    step: str
    reasons: list[str]


@dataclass
class EventResult:
    t: float
    action: str | None
    step_id: str | None
    map_score: float
    decision: str
    message: str
    reasons: list[str]
    completed_after: list[str]


@dataclass
class ReplayReport:
    order_id: str
    findings: list[Finding] = field(default_factory=list)
    events: list[EventResult] = field(default_factory=list)
    completed: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)


def load_session(path: str | Path) -> list[SessionEvent]:
    """Load session JSON.

    Accepts either mapped step ids::

        {"t": 0, "step": "STEP-01", "hands_clear": true}

    or M³-HRC-style action labels::

        {"t": 0, "action": "take rpi CM", "hands_clear": true}
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    events: list[SessionEvent] = []
    for item in raw.get("events", []):
        events.append(
            SessionEvent(
                t=float(item["t"]),
                step=str(item["step"]) if item.get("step") else None,
                action=str(item["action"]) if item.get("action") else None,
                hands_clear=bool(item.get("hands_clear", True)),
            )
        )
    return events


def replay(
    steps: dict[str, Step],
    events: list[SessionEvent],
    order_id: str = "WO-replay",
) -> list[Finding]:
    """Backward-compatible: return only violation findings."""
    return replay_report(steps, events, order_id=order_id).findings


def replay_report(
    steps: dict[str, Step],
    events: list[SessionEvent],
    order_id: str = "WO-replay",
) -> ReplayReport:
    """Walk events; map actions; decide ACT/WAIT/GUIDE; complete only on ACT."""
    order = WorkOrder(id=order_id)
    report = ReplayReport(order_id=order_id)
    counts = {"ACT": 0, "WAIT": 0, "GUIDE": 0}

    for ev in events:
        step_id = ev.step
        map_score = 1.0 if step_id else 0.0
        raw_action = ev.action

        if step_id is None and raw_action:
            step_id, map_score = map_action_to_step(raw_action, steps)

        step = steps.get(step_id) if step_id else None
        ctx = ShopContext(hands_clear=ev.hands_clear)
        decision: Decision = decide(step, order, ctx, raw_action=raw_action)

        if decision.kind == "ACT" and step is not None:
            complete_step(order, step, ctx)
        elif decision.kind != "ACT":
            report.findings.append(
                Finding(
                    t=ev.t,
                    step=step_id or (raw_action or "?"),
                    reasons=decision.reasons or [decision.kind.lower()],
                )
            )

        counts[decision.kind] = counts.get(decision.kind, 0) + 1
        report.events.append(
            EventResult(
                t=ev.t,
                action=raw_action,
                step_id=step_id,
                map_score=round(map_score, 3),
                decision=decision.kind,
                message=decision.message,
                reasons=decision.reasons,
                completed_after=sorted(order.completed),
            )
        )

    report.completed = sorted(order.completed)
    report.counts = counts
    return report


def findings_as_dicts(findings: list[Finding]) -> list[dict[str, Any]]:
    return [{"t": f.t, "step": f.step, "reasons": f.reasons} for f in findings]


def report_as_dict(report: ReplayReport) -> dict[str, Any]:
    return {
        "order_id": report.order_id,
        "counts": report.counts,
        "completed": report.completed,
        "findings": findings_as_dicts(report.findings),
        "events": [asdict(e) for e in report.events],
    }
