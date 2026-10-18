"""CLI: check, retrieve, replay, decide."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import ShopContext, WorkOrder, can_start, parse_sop
from .bridge import from_decision, to_ros_fields
from .decide import decide
from .map_actions import map_action_to_step
from .next import ready_steps
from .eval_suite import (
    eval_retrieve_full,
    eval_replay_full,
    format_summary,
    run_suite,
)
from .rag import hits_as_dicts, hybrid_retrieve
from .replay import load_session, report_as_dict, replay_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOP = ROOT / "docs" / "sop_samples" / "miam_assembly_subset.md"
DEFAULT_EVAL = ROOT / "docs" / "eval" / "sop_qa.json"
A101_SOP = ROOT / "docs" / "sop_samples" / "assembly101_toy_subset.md"
A101_EVAL = ROOT / "docs" / "eval" / "assembly101_qa.json"
A101_SESSION = ROOT / "docs" / "sessions" / "assembly101_9033_c02a.csv"
RESULTS = ROOT / "docs" / "eval" / "results" / "latest.json"


def _cmd_check(args: argparse.Namespace) -> int:
    steps = parse_sop(args.sop)
    completed = {s.strip() for s in args.done.split(",") if s.strip()}
    order = WorkOrder(id="WO-cli", completed=completed)
    ctx = ShopContext(hands_clear=args.hands_clear)
    ok, reasons = can_start(steps[args.step], order, ctx)
    print(json.dumps({"ok": ok, "reasons": reasons}))
    return 0 if ok else 1


def _cmd_retrieve(args: argparse.Namespace) -> int:
    hits = hybrid_retrieve(
        args.sop,
        args.query,
        top_k=args.top_k,
        min_score=args.min_score,
        use_embeddings=not args.no_embeddings,
    )
    print(json.dumps(hits_as_dicts(hits), indent=2))
    return 0


def _cmd_eval_retrieve(args: argparse.Namespace) -> int:
    report = eval_retrieve_full(args.sop, args.cases, top_k=args.top_k)
    print(json.dumps(report, indent=2))
    return 0 if report["metrics"]["hit_at_1"] >= args.min_hit_at_1 else 1


def _cmd_eval_replay(args: argparse.Namespace) -> int:
    sop = args.sop
    if "assembly101" in Path(args.session).name and Path(args.sop) == DEFAULT_SOP:
        sop = A101_SOP
    report = eval_replay_full(sop, args.session)
    print(json.dumps(report, indent=2))
    return 0


def _cmd_eval(args: argparse.Namespace) -> int:
    suite = run_suite(
        miam_sop=ROOT / "docs" / "sop_samples" / "miam_assembly_subset.md",
        miam_cases=DEFAULT_EVAL,
        a101_sop=A101_SOP,
        a101_cases=A101_EVAL,
        a101_session=A101_SESSION,
        top_k=args.top_k,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(suite, indent=2), encoding="utf-8")
    print(format_summary(suite))
    print(f"wrote {out}")
    ok = (
        suite["summary"]["miam_retrieve_hit_at_1"] >= args.min_hit_at_1
        and suite["summary"]["assembly101_retrieve_hit_at_1"] >= args.min_hit_at_1
    )
    return 0 if ok else 1


def _cmd_replay(args: argparse.Namespace) -> int:
    steps = parse_sop(args.sop)
    events = load_session(args.session)
    report = replay_report(steps, events)
    print(json.dumps(report_as_dict(report), indent=2))
    return 0 if report.counts.get("WAIT", 0) + report.counts.get("GUIDE", 0) == 0 else 1


def _resolve_decision(args: argparse.Namespace):
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
    return d, map_score


def _cmd_decide(args: argparse.Namespace) -> int:
    d, map_score = _resolve_decision(args)
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


def _cmd_emit(args: argparse.Namespace) -> int:
    d, _ = _resolve_decision(args)
    cmd = from_decision(d)
    print(json.dumps(to_ros_fields(cmd), indent=2))
    return 0 if d.kind == "ACT" else 1


def _cmd_next(args: argparse.Namespace) -> int:
    steps = parse_sop(args.sop)
    completed = {s.strip() for s in args.done.split(",") if s.strip()}
    order = WorkOrder(id="WO-cli", completed=completed)
    ctx = ShopContext(hands_clear=args.hands_clear)
    ready = ready_steps(steps, order, ctx)
    print(
        json.dumps(
            {
                "ready": ready,
                "titles": {sid: steps[sid].title for sid in ready},
            },
            indent=2,
        )
    )
    return 0


def _cmd_ask(args: argparse.Namespace) -> int:
    from .agent import ask

    try:
        out = ask(args.question, sop_path=args.sop, model=args.model)
    except RuntimeError as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
    print(json.dumps(out, indent=2))
    return 0


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

    p_ret = sub.add_parser("retrieve", help="hybrid SOP search with citations")
    p_ret.add_argument("query")
    p_ret.add_argument("--top-k", type=int, default=3)
    p_ret.add_argument("--min-score", type=float, default=0.0)
    p_ret.add_argument(
        "--no-embeddings",
        action="store_true",
        help="force local dense channel (skip OpenAI embeddings)",
    )
    p_ret.set_defaults(func=_cmd_retrieve)

    p_eval = sub.add_parser("eval-retrieve", help="retrieve metrics (hit@1, hit@k, MRR)")
    p_eval.add_argument("--cases", type=Path, default=DEFAULT_EVAL)
    p_eval.add_argument("--top-k", type=int, default=3)
    p_eval.add_argument("--min-hit-at-1", type=float, default=0.7)
    p_eval.set_defaults(func=_cmd_eval_retrieve)

    p_eval_r = sub.add_parser("eval-replay", help="replay compliance + label agreement")
    p_eval_r.add_argument("session", type=Path, nargs="?", default=A101_SESSION)
    p_eval_r.set_defaults(func=_cmd_eval_replay)

    p_eval_all = sub.add_parser("eval", help="full suite + write results JSON")
    p_eval_all.add_argument("--top-k", type=int, default=3)
    p_eval_all.add_argument("--min-hit-at-1", type=float, default=0.7)
    p_eval_all.add_argument("--out", type=Path, default=RESULTS)
    p_eval_all.set_defaults(func=_cmd_eval)

    p_rep = sub.add_parser("replay", help="replay a session JSON (action or step labels)")
    p_rep.add_argument("session", type=Path)
    p_rep.set_defaults(func=_cmd_replay)

    p_dec = sub.add_parser("decide", help="ACT / WAIT / GUIDE for one observation")
    p_dec.add_argument("--step", default=None, help="STEP-06")
    p_dec.add_argument("--action", default=None, help="free-text action label")
    p_dec.add_argument("--done", default="", help="comma-separated completed step ids")
    p_dec.add_argument("--hands-clear", action="store_true")
    p_dec.set_defaults(func=_cmd_decide)

    p_emit = sub.add_parser("emit", help="ROS-ready command JSON for one observation")
    p_emit.add_argument("--step", default=None, help="STEP-06")
    p_emit.add_argument("--action", default=None, help="free-text action label")
    p_emit.add_argument("--done", default="", help="comma-separated completed step ids")
    p_emit.add_argument("--hands-clear", action="store_true")
    p_emit.set_defaults(func=_cmd_emit)

    p_next = sub.add_parser("next", help="list steps that can start now")
    p_next.add_argument("--done", default="", help="comma-separated completed step ids")
    p_next.add_argument("--hands-clear", action="store_true")
    p_next.set_defaults(func=_cmd_next)

    p_ask = sub.add_parser("ask", help="LLM + tools (needs OPENAI_API_KEY)")
    p_ask.add_argument("question")
    p_ask.add_argument("--model", default=None)
    p_ask.set_defaults(func=_cmd_ask)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
