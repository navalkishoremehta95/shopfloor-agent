"""Tests for checks, retrieve, replay, tools."""

from pathlib import Path

from shopfloor import ShopContext, WorkOrder, can_start, complete_step, parse_sop, retrieve
from shopfloor.replay import load_session, replay
from shopfloor.tools import TOOL_SPECS, run_tool


ROOT = Path(__file__).resolve().parents[1]
SOP = ROOT / "docs" / "sop_samples" / "miam_assembly_subset.md"
SESSION = ROOT / "docs" / "sessions" / "sample_miam_subset.json"


def test_parse_has_ten_steps():
    steps = parse_sop(SOP)
    assert len(steps) == 10
    assert steps["STEP-06"].risk == "high"
    assert steps["STEP-06"].pred == ["STEP-05"]


def test_step06_blocked_when_hands_busy():
    steps = parse_sop(SOP)
    order = WorkOrder(
        id="WO-t1",
        completed={f"STEP-{i:02d}" for i in range(1, 6)},
    )
    ctx = ShopContext(hands_clear=False)
    ok, reasons = can_start(steps["STEP-06"], order, ctx)
    assert ok is False
    assert "hands not clear" in reasons


def test_step06_ok_when_hands_clear():
    steps = parse_sop(SOP)
    order = WorkOrder(
        id="WO-t2",
        completed={f"STEP-{i:02d}" for i in range(1, 6)},
    )
    ctx = ShopContext(hands_clear=True)
    ok, reasons = complete_step(order, steps["STEP-06"], ctx)
    assert ok is True
    assert "STEP-06" in order.completed


def test_retrieve_prefers_fastening_step():
    hits = retrieve(SOP, "high risk fastening screwdriver hands", top_k=3)
    assert hits
    assert hits[0][0] == "STEP-06"
    assert hits[0][1] > 0


def test_retrieve_title_boost_for_display():
    hits = retrieve(SOP, "where do I put the display", top_k=2)
    assert hits
    assert hits[0][0] in {"STEP-09", "STEP-10"}


def test_retrieve_min_score_filters_weak_hits():
    weak = retrieve(SOP, "display", top_k=5, min_score=0.0)
    strong = retrieve(SOP, "display", top_k=5, min_score=0.5)
    assert len(strong) <= len(weak)
    assert all(score >= 0.5 for _, score, _ in strong)


def test_replay_flags_hands_busy_on_step06():
    steps = parse_sop(SOP)
    events = load_session(SESSION)
    findings = replay(steps, events)
    assert findings
    assert findings[0].step == "STEP-06"
    assert "hands not clear" in findings[0].reasons
    # second STEP-06 attempt is clear; session should finish without more hits
    assert len(findings) == 1


def test_tool_check_and_retrieve():
    steps = parse_sop(SOP)
    done = [f"STEP-{i:02d}" for i in range(1, 6)]
    blocked = run_tool(
        "check_can_start",
        {"step_id": "STEP-06", "completed": done, "hands_clear": False},
        steps=steps,
        sop_path=SOP,
    )
    assert blocked["ok"] is False

    hits = run_tool(
        "retrieve_sop",
        {"query": "high risk fastening screwdriver", "top_k": 1},
        steps=steps,
        sop_path=SOP,
    )
    assert hits["hits"][0]["step_id"] == "STEP-06"
    assert {t["name"] for t in TOOL_SPECS} >= {
        "check_can_start",
        "complete_step",
        "retrieve_sop",
    }
