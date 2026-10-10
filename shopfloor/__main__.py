"""CLI: check, retrieve, replay, decide."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import ShopContext, WorkOrder, can_start, parse_sop, retrieve
from .decide import decide
from .map_actions import map_action_to_step
from .replay import load_session, report_as_dict, replay_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOP = ROOT / "docs" / "sop_samples" / "miam_assembly_subset.md"


def _cmd_check(args: argparse.Namespace) -> int:
    steps = parse_sop(args.sop)
    completed = {s.strip() for s in args.done.split(",") if s.strip()}
    order = WorkOrder(id="WO-cli", completed=completed)
    ctx = ShopContext(hands_clear=args.hands_clear)
    ok, reasons = can_start(steps[args.step], order, ctx)
    print(json.dumps({"ok": ok, "reasons": reasons}))
    return 0 if ok else 1


def _cmd_retrieve(args: argparse.Namespace) -> int:
    hits = retrieve(args.sop, args.query, top_k=args.top_k, min_score=args.min_score)
    out = [
        {"step_id": sid, "score": round(score, 3), "title": body.splitlines()[0]}
        for sid, score, body in hits
    ]
    print(json.dumps(out, indent=2))
    return 0


def _cmd_replay(args: argparse.Namespace) -> int:
    steps = parse_sop(args.sop)
    events = load_session(args.session)
    report = replay_report(steps, events)
    print(json.dumps(report_as_dict(report), indent=2))
    return 0 if report.counts.get("WAIT", 0) + report.counts.get("GUIDE", 0) == 0 else 1


def _cmd_decide(args: argparse.Namespace) -> int:
    steps = parse_sop(args.sop)
    completed = {s.strip() for s in args.done.split(",") if s.strip()}
    order = WorkOrder(id="WO-cli", completed=completed)
    ctx = ShopContext(hands_clear=args.hands_clear)

    step_id = args.step
    raw_action = args.action
    map_score = 1.0
    if not step_id and raw_action:
        step_id, map_score = map_action_to_step(raw_action, steps)
    step = steps.get(step_id) if step_id else None
    d = decide(step, order, ctx, raw_action=raw_action)
    print(
        json.dumps(
            {
                "decision": d.kind,
                "step_id": d.step_id,
                "map_score": round(map_score, 3),
                "reasons": d.reasons,
                "message": d.message,
            },
            indent=2,
        )
    )
    return 0 if d.kind == "ACT" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="shopfloor", description="SOP procedure checks")
    parser.add_argument(
        "--sop",
        type=Path,
        default=DEFAULT_SOP,
        help="path to SOP markdown",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check", help="can_start for one step")
    p_check.add_argument("step", help="e.g. STEP-06")
    p_check.add_argument("--done", default="", help="comma-separated completed step ids")
    p_check.add_argument("--hands-clear", action="store_true")
    p_check.set_defaults(func=_cmd_check)

    p_ret = sub.add_parser("retrieve", help="search SOP")
    p_ret.add_argument("query")
    p_ret.add_argument("--top-k", type=int, default=3)
    p_ret.add_argument("--min-score", type=float, default=0.0)
    p_ret.set_defaults(func=_cmd_retrieve)

    p_rep = sub.add_parser("replay", help="replay a session JSON (action or step labels)")
    p_rep.add_argument("session", type=Path)
    p_rep.set_defaults(func=_cmd_replay)

    p_dec = sub.add_parser("decide", help="ACT / WAIT / GUIDE for one observation")
    p_dec.add_argument("--step", default=None, help="STEP-06")
    p_dec.add_argument("--action", default=None, help="free-text action label")
    p_dec.add_argument("--done", default="", help="comma-separated completed step ids")
    p_dec.add_argument("--hands-clear", action="store_true")
    p_dec.set_defaults(func=_cmd_decide)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
