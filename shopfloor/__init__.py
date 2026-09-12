"""Small helpers for procedure checks.

Order first, then safety for high-risk steps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Step:
    id: str
    title: str
    pred: list[str] = field(default_factory=list)
    risk: str = "low"


@dataclass
class WorkOrder:
    id: str
    completed: set[str] = field(default_factory=set)


@dataclass
class ShopContext:
    # shared bench: True only when operator hands are out of the zone
    hands_clear: bool = False


def is_allowed(step: Step, order: WorkOrder) -> tuple[bool, set[str]]:
    """Order check: Pred(s) subset of C."""
    missing = set(step.pred) - order.completed
    return len(missing) == 0, missing


def can_start(step: Step, order: WorkOrder, ctx: ShopContext) -> tuple[bool, list[str]]:
    """Order + safety. Returns (ok, reasons)."""
    reasons: list[str] = []

    ok_order, missing = is_allowed(step, order)
    if not ok_order:
        reasons.append("missing: " + ", ".join(sorted(missing)))

    if step.risk == "high" and not ctx.hands_clear:
        reasons.append("hands not clear")

    return len(reasons) == 0, reasons


def complete_step(
    order: WorkOrder, step: Step, ctx: ShopContext
) -> tuple[bool, list[str]]:
    ok, reasons = can_start(step, order, ctx)
    if not ok:
        return False, reasons
    order.completed.add(step.id)
    return True, []


def parse_sop(path: str | Path) -> dict[str, Step]:
    """Parse the markdown SOP used in docs/sop_samples."""
    text = Path(path).read_text(encoding="utf-8")
    steps: dict[str, Step] = {}

    for block in text.split("## ")[1:]:
        lines = [ln.strip() for ln in block.strip().splitlines() if ln.strip()]
        if not lines:
            continue

        head = lines[0]
        step_id, _, title = head.partition(" ")
        pred: list[str] = []
        risk = "low"

        for line in lines[1:]:
            if line.startswith("Depends on "):
                rest = line.removeprefix("Depends on ").strip()
                pred.append(rest.split()[0].rstrip("."))
            if "High risk" in line:
                risk = "high"

        steps[step_id] = Step(id=step_id, title=title, pred=pred, risk=risk)

    return steps
