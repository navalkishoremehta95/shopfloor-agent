"""Steps that may start given current order and shop context."""

from __future__ import annotations

from . import ShopContext, Step, WorkOrder, can_start


def ready_steps(
    steps: dict[str, Step],
    order: WorkOrder,
    ctx: ShopContext,
) -> list[str]:
    ready: list[str] = []
    for sid in sorted(steps):
        step = steps[sid]
        if sid in order.completed:
            continue
        ok, _ = can_start(step, order, ctx)
        if ok:
            ready.append(sid)
    return ready
