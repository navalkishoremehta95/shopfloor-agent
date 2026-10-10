"""Optional LLM loop over shopfloor tools (OpenAI-compatible API)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from . import Step, parse_sop
from .tools import openai_tools, run_tool


SYSTEM = (
    "You assist with procedure-compliant industrial assembly (MIAM / M3-HRC). "
    "Use tools for SOP facts and ACT/WAIT/GUIDE decisions. "
    "Do not invent safety outcomes; trust tool results."
)


def ask(
    question: str,
    *,
    sop_path: str | Path,
    steps: dict[str, Step] | None = None,
    model: str | None = None,
    max_rounds: int = 4,
) -> dict[str, Any]:
    """Run a short tool-calling chat. Needs OPENAI_API_KEY."""
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install openai: pip install openai") from exc

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY")

    sop_path = Path(sop_path)
    steps = steps or parse_sop(sop_path)
    client = OpenAI(api_key=api_key)
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]
    trace: list[dict[str, Any]] = []
    tools = openai_tools()

    for _ in range(max_rounds):
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        msg = resp.choices[0].message
        tool_calls = msg.tool_calls or []
        if not tool_calls:
            answer = (msg.content or "").strip()
            return {"answer": answer, "trace": trace, "model": model}

        messages.append(
            {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ],
            }
        )
        for tc in tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result = run_tool(name, args, steps=steps, sop_path=sop_path)
            trace.append({"tool": name, "args": args, "result": result})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                }
            )

    return {
        "answer": "Stopped after max tool rounds.",
        "trace": trace,
        "model": model,
    }
