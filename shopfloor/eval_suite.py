"""Retrieve + replay evaluation summaries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import parse_sop
from .rag import eval_retrieve, hybrid_retrieve
from .replay import load_session, replay_report


def _mrr(ranked: list[str], expect: set[str]) -> float:
    for i, sid in enumerate(ranked, start=1):
        if sid in expect:
            return 1.0 / i
    return 0.0


def eval_retrieve_full(
    sop_path: str | Path,
    cases_path: str | Path,
    *,
    top_k: int = 3,
) -> dict[str, Any]:
    base = eval_retrieve(sop_path, cases_path, top_k=top_k)
    cases = json.loads(Path(cases_path).read_text(encoding="utf-8"))["cases"]
    mrr_sum = 0.0
    fails: list[dict[str, Any]] = []
    for case, row in zip(cases, base["cases"]):
        hits = hybrid_retrieve(
            sop_path, case["query"], top_k=top_k, use_embeddings=False
        )
        ranked = [h.step_id for h in hits]
        expect = set(case["expect"])
        score = _mrr(ranked, expect)
        mrr_sum += score
        row["mrr"] = round(score, 3)
        row["scores"] = [round(h.score, 3) for h in hits]
        if not row["hit_at_1"]:
            fails.append(
                {
                    "id": row["id"],
                    "query": row["query"],
                    "expect": row["expect"],
                    "got": row["got"],
                }
            )
    n = base["n"] or 1
    return {
        "task": "retrieve",
        "sop": str(sop_path),
        "cases": str(cases_path),
        "params": {
            "top_k": top_k,
            "use_embeddings": False,
            "lexical_weight": 0.65,
            "dense": "char-3gram",
        },
        "metrics": {
            "n": base["n"],
            "hit_at_1": base["hit_at_1"],
            "hit_at_k": base["hit_at_k"],
            "mrr": round(mrr_sum / n, 3),
            "fail_count": len(fails),
        },
        "failures": fails,
        "cases_detail": base["cases"],
    }


def eval_replay_full(
    sop_path: str | Path,
    session_path: str | Path,
) -> dict[str, Any]:
    steps = parse_sop(sop_path)
    events = load_session(session_path)
    report = replay_report(steps, events)
    n = len(report.events) or 1
    counts = report.counts
    # optional agreement with Assembly101-style src_label on CSV
    tp = fp = tn = fn = 0
    labeled = 0
    for ev, raw in zip(report.events, _raw_labels(session_path)):
        if raw is None:
            continue
        labeled += 1
        is_mistake = raw not in {"correct", "correction", ""}
        predicted_block = ev.decision in {"GUIDE", "WAIT"}
        if is_mistake and predicted_block:
            tp += 1
        elif is_mistake and not predicted_block:
            fn += 1
        elif (not is_mistake) and predicted_block:
            fp += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (
        (2 * precision * recall / (precision + recall))
        if precision is not None and recall is not None and (precision + recall)
        else None
    )

    return {
        "task": "replay",
        "sop": str(sop_path),
        "session": str(session_path),
        "params": {"map": "action→STEP token overlap", "decide": "ACT|WAIT|GUIDE"},
        "metrics": {
            "n_events": len(report.events),
            "n_steps_completed": len(report.completed),
            "act_rate": round(counts.get("ACT", 0) / n, 3),
            "wait_rate": round(counts.get("WAIT", 0) / n, 3),
            "guide_rate": round(counts.get("GUIDE", 0) / n, 3),
            "violation_findings": len(report.findings),
            "completed": report.completed,
            "counts": counts,
        },
        "label_agreement": {
            "n_labeled": labeled,
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
            "precision": None if precision is None else round(precision, 3),
            "recall": None if recall is None else round(recall, 3),
            "f1": None if f1 is None else round(f1, 3),
            "note": "mistake/wrong-order labels vs GUIDE|WAIT (when src_label present)",
        },
        "findings": [
            {"t": f.t, "step": f.step, "reasons": f.reasons} for f in report.findings
        ],
    }


def _raw_labels(session_path: str | Path) -> list[str | None]:
    path = Path(session_path)
    if path.suffix.lower() != ".csv":
        return []
    import csv

    labels: list[str | None] = []
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if not row or not any((v or "").strip() for v in row.values()):
                continue
            # mirror attach-only filter used by importer consumers
            action = (row.get("action") or "").strip().lower()
            if action.startswith("detach"):
                continue
            labels.append((row.get("src_label") or "").strip() or None)
    return labels


def run_suite(
    *,
    miam_sop: Path,
    miam_cases: Path,
    a101_sop: Path,
    a101_cases: Path,
    a101_session: Path,
    top_k: int = 3,
) -> dict[str, Any]:
    retrieve_miam = eval_retrieve_full(miam_sop, miam_cases, top_k=top_k)
    retrieve_a101 = eval_retrieve_full(a101_sop, a101_cases, top_k=top_k)
    replay_a101 = eval_replay_full(a101_sop, a101_session)
    return {
        "summary": {
            "miam_retrieve_hit_at_1": retrieve_miam["metrics"]["hit_at_1"],
            "miam_retrieve_mrr": retrieve_miam["metrics"]["mrr"],
            "assembly101_retrieve_hit_at_1": retrieve_a101["metrics"]["hit_at_1"],
            "assembly101_retrieve_mrr": retrieve_a101["metrics"]["mrr"],
            "assembly101_replay_guide_rate": replay_a101["metrics"]["guide_rate"],
            "assembly101_mistake_f1": replay_a101["label_agreement"]["f1"],
        },
        "retrieve_miam": retrieve_miam,
        "retrieve_assembly101": retrieve_a101,
        "replay_assembly101": replay_a101,
    }


def format_summary(suite: dict[str, Any]) -> str:
    s = suite["summary"]
    lines = [
        "ShopFloor eval summary",
        "----------------------",
        f"MIAM retrieve     hit@1={s['miam_retrieve_hit_at_1']}  mrr={s['miam_retrieve_mrr']}",
        f"A101 retrieve     hit@1={s['assembly101_retrieve_hit_at_1']}  mrr={s['assembly101_retrieve_mrr']}",
        f"A101 replay       guide_rate={s['assembly101_replay_guide_rate']}  mistake_f1={s['assembly101_mistake_f1']}",
    ]
    return "\n".join(lines)
