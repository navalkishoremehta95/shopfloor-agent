"""Tool wrappers. The model proposes; these helpers decide."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import ShopContext, Step, WorkOrder, can_start, complete_step
from .decide import decide
from .map_actions import map_action_to_step
from .next import ready_steps
from .rag import hits_as_dicts, hybrid_retrieve


TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "retrieve_sop",
        "description": "Hybrid SOP search with citations (lexical + dense).",
        "parameters": {
            "query": {"type": "string"},
            "top_k": {"type": "integer", "default": 3},
        },
    },
    {
        "name": "decide_action",
        "description": "Return ACT, WAIT, or GUIDE for a step or free-text action.",
        "parameters": {
            "step_id": {"type": "string"},
            "action": {"type": "string"},
            "completed": {"type": "array", "items": {"type": "string"}},
            "hands_clear": {"type": "boolean"},
        },
    },
    {
        "name": "list_ready_steps",
        "description": "List SOP steps that may start now.",
        "parameters": {
            "completed": {"type": "array", "items": {"type": "string"}},
            "hands_clear": {"type": "boolean"},
        },
    },
    {
        "name": "check_can_start",
        "description": "Low-level order/safety check for one step id.",
        "parameters": {
            "step_id": {"type": "string"},
            "completed": {"type": "array", "items": {"type": "string"}},
            "hands_clear": {"type": "boolean"},
        },
    },
    {
        "name": "complete_step",
        "description": "Mark a step complete if allowed.",
        "parameters": {
            "step_id": {"type": "string"},
            "completed": {"type": "array", "items": {"type": "string"}},
            "hands_clear": {"type": "boolean"},
        },
    },
]


def openai_tools() -> list[dict[str, Any]]:
    """OpenAI-compatible tool schemas from TOOL_SPECS."""
    out: list[dict[str, Any]] = []
    for spec in TOOL_SPECS:
        props = {}
        required = []
        for key, schema in spec["parameters"].items():
            if isinstance(schema, dict):
                props[key] = schema
            else:
                props[key] = {"type": "string", "description": str(schema)}
            if key in {"query", "step_id"} or (
                spec["name"] == "decide_action" and key in {"completed", "hands_clear"}
            ):
                pass
        # require only the essentials per tool
        if spec["name"] == "retrieve_sop":
            required = ["query"]
        elif spec["name"] == "decide_action":
            required = ["completed", "hands_clear"]
        elif spec["name"] in {"list_ready_steps"}:
            required = ["completed", "hands_clear"]
        elif spec["name"] in {"check_can_start", "complete_step"}:
            required = ["step_id", "completed", "hands_clear"]
        out.append(
            {
                "type": "function",
                "function": {
                    "name": spec["name"],
                    "description": spec["description"],
                    "parameters": {
                        "type": "object",
                        "properties": props,
                        "required": required,
                    },
                },
            }
        )
    return out


def run_tool(
    name: str,
    args: dict[str, Any],
    *,
    steps: dict[str, Step],
    sop_path: str | Path,
) -> dict[str, Any]:
    if name == "retrieve_sop":
        hits = hybrid_retrieve(
            sop_path,
            str(args["query"]),
            top_k=int(args.get("top_k", 3)),
            min_score=float(args.get("min_score", 0.0)),
        )
        return {"hits": hits_as_dicts(hits)}

    if name == "decide_action":
        completed = set(args.get("completed") or [])
        order = WorkOrder(id="WO-tool", completed=completed)
        ctx = ShopContext(hands_clear=bool(args.get("hands_clear", False)))
        step_id = args.get("step_id")
        raw_action = args.get("action")
        map_score = 1.0
        if not step_id and raw_action:
            step_id, map_score = map_action_to_step(str(raw_action), steps)
        step = steps.get(step_id) if step_id else None
        d = decide(step, order, ctx, raw_action=raw_action)
        return {
            "decision": d.kind,
            "step_id": d.step_id,
            "map_score": round(map_score, 3),
            "reasons": d.reasons,
            "message": d.message,
        }

    if name == "list_ready_steps":
        order = WorkOrder(
            id="WO-tool",
            completed=set(args.get("completed") or []),
        )
        ctx = ShopContext(hands_clear=bool(args.get("hands_clear", False)))
        ready = ready_steps(steps, order, ctx)
        return {
            "ready": ready,
            "titles": {sid: steps[sid].title for sid in ready},
        }

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

    return {"error": f"unknown tool: {name}"}
