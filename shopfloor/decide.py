"""High-level ACT / WAIT / GUIDE decision for one step attempt."""

from __future__ import annotations

from dataclasses import dataclass

from . import ShopContext, Step, WorkOrder, can_start


@dataclass
class Decision:
    kind: str  # ACT | WAIT | GUIDE
    step_id: str | None
    reasons: list[str]
    message: str


def decide(
    step: Step | None,
    order: WorkOrder,
    ctx: ShopContext,
    *,
    raw_action: str | None = None,
) -> Decision:
    """Decide what the agent should do for the current observation."""
    if step is None:
        hint = f" ({raw_action})" if raw_action else ""
        return Decision(
            kind="GUIDE",
            step_id=None,
            reasons=["unknown action"],
            message=f"Unrecognized action{hint}. Check SOP wording or label map.",
        )

    ok, reasons = can_start(step, order, ctx)
    if ok:
        return Decision(
            kind="ACT",
            step_id=step.id,
            reasons=[],
            message=f"{step.id} ready — proceed.",
        )

    if any("hands not clear" in r for r in reasons) and not any(
        r.startswith("missing:") for r in reasons
    ):
        return Decision(
            kind="WAIT",
            step_id=step.id,
            reasons=reasons,
            message=f"Wait — hands still in shared zone for {step.id}.",
        )

    # missing predecessors (and any mixed case) → guide the operator
    missing = []
    for r in reasons:
        if r.startswith("missing:"):
            missing.append(r.removeprefix("missing:").strip())
    if missing:
        return Decision(
            kind="GUIDE",
            step_id=step.id,
            reasons=reasons,
            message=f"Do {missing[0]} before {step.id}.",
        )

    return Decision(
        kind="GUIDE",
        step_id=step.id,
        reasons=reasons,
        message=f"Blocked on {step.id}: {', '.join(reasons)}",
    )
