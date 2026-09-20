"""Basic checks for shopfloor helpers."""

from pathlib import Path

from shopfloor import ShopContext, WorkOrder, can_start, complete_step, parse_sop, retrieve


ROOT = Path(__file__).resolve().parents[1]
SOP = ROOT / "docs" / "sop_samples" / "miam_assembly_subset.md"


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
