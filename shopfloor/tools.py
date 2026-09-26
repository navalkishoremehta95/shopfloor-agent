"""Tool wrappers for an LLM agent.

The model may propose; these helpers decide.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import ShopContext, Step, WorkOrder, can_start, complete_step, retrieve


TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "check_can_start",
        "description": "Check if a step may start given completed steps and hands_clear.",
        "parameters": {
            "step_id": "string",
            "completed": "list of step ids",
            "hands_clear": "bool",
        },
    },
    {
        "name": "complete_step",
        "description": "Mark a step complete if can_start allows it.",
        "parameters": {
            "step_id": "string",
            "completed": "list of step ids",
            "hands_clear": "bool",
        },
    },
    {
        "name": "retrieve_sop",
        "description": "Search SOP text by token overlap.",
        "parameters": {
            "query": "string",
            "top_k": "int, default 3",
            "min_score": "float, default 0.0",
        },
    },
]


def run_tool(
    name: str,
    args: dict[str, Any],
    *,
    steps: dict[str, Step],
    sop_path: str | Path,
) -> dict[str, Any]:
    if name == "check_can_start":
        step_id = args["step_id"]
        order = WorkOrder(
            id="WO-tool",
            completed=set(args.get("completed") or []),
        )
        ctx = ShopContext(hands_clear=bool(args.get("hands_clear", False)))
        ok, reasons = can_start(steps[step_id], order, ctx)
        return {"ok": ok, "reasons": reasons}

    if name == "complete_step":
        step_id = args["step_id"]
        order = WorkOrder(
            id="WO-tool",
            completed=set(args.get("completed") or []),
        )
        ctx = ShopContext(hands_clear=bool(args.get("hands_clear", False)))
        ok, reasons = complete_step(order, steps[step_id], ctx)
        return {
            "ok": ok,
            "reasons": reasons,
            "completed": sorted(order.completed),
        }

    if name == "retrieve_sop":
        hits = retrieve(
            sop_path,
            str(args["query"]),
            top_k=int(args.get("top_k", 3)),
            min_score=float(args.get("min_score", 0.0)),
        )
        return {
            "hits": [
                {"step_id": sid, "score": round(score, 3), "title": body.splitlines()[0]}
                for sid, score, body in hits
            ]
        }

    return {"error": f"unknown tool: {name}"}
