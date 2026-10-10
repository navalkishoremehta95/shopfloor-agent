"""Map free-text action labels onto SOP step ids."""

from __future__ import annotations

from . import Step, _tokens


def map_action_to_step(
    action: str,
    steps: dict[str, Step],
    *,
    min_score: float = 0.34,
) -> tuple[str | None, float]:
    """Best step id for an action string, or (None, 0) if weak."""
    q = _tokens(action)
    if not q:
        return None, 0.0

    best_id: str | None = None
    best = 0.0
    for sid, step in steps.items():
        title_toks = _tokens(f"{step.id} {step.title}")
        overlap = q & title_toks
        if not overlap:
            continue
        score = len(overlap) / len(q)
        # exact title phrase boost
        if step.title.lower() in action.lower() or action.lower() in step.title.lower():
            score = min(1.0, score + 0.35)
        if score > best:
            best = score
            best_id = sid

    if best < min_score:
        return None, best
    return best_id, best
