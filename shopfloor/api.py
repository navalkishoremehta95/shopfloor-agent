"""HTTP API for retrieve / decide / next."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import ShopContext, WorkOrder, parse_sop
from .bridge import from_decision, to_ros_fields
from .decide import decide
from .map_actions import map_action_to_step
from .metrics import log_event
from .next import ready_steps
from .rag import hits_as_dicts, hybrid_retrieve

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOP = ROOT / "docs" / "sop_samples" / "miam_assembly_subset.md"

_steps = None
_sop = DEFAULT_SOP


def _load(sop: Path | None = None):
    global _steps, _sop
    path = sop or _sop
    _sop = path
    _steps = parse_sop(path)
    return _steps


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    _load()
    yield


app = FastAPI(title="ShopFloor Agent", version="0.1.0", lifespan=_lifespan)


class RetrieveIn(BaseModel):
    query: str
    top_k: int = 3
    min_score: float = 0.0
    use_embeddings: bool = False


class DecideIn(BaseModel):
    step_id: str | None = None
    action: str | None = None
    completed: list[str] = Field(default_factory=list)
    hands_clear: bool = False


class NextIn(BaseModel):
    completed: list[str] = Field(default_factory=list)
    hands_clear: bool = False


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/retrieve")
def api_retrieve(body: RetrieveIn) -> dict[str, Any]:
    steps = _steps or _load()
    t0 = time.perf_counter()
    hits = hybrid_retrieve(
        _sop,
        body.query,
        top_k=body.top_k,
        min_score=body.min_score,
        use_embeddings=body.use_embeddings,
    )
    ms = (time.perf_counter() - t0) * 1000
    log_event("retrieve", {"query": body.query, "n": len(hits), "ms": round(ms, 1)})
    return {"hits": hits_as_dicts(hits), "latency_ms": round(ms, 1)}


@app.post("/decide")
def api_decide(body: DecideIn) -> dict[str, Any]:
    steps = _steps or _load()
    order = WorkOrder(id="WO-api", completed=set(body.completed))
    ctx = ShopContext(hands_clear=body.hands_clear)
    step_id = body.step_id
    map_score = 1.0
    if not step_id and body.action:
        step_id, map_score = map_action_to_step(body.action, steps)
    step = steps.get(step_id) if step_id else None
    if body.step_id and step is None:
        raise HTTPException(status_code=404, detail=f"unknown step: {body.step_id}")
    d = decide(step, order, ctx, raw_action=body.action)
    out = {
        "decision": d.kind,
        "step_id": d.step_id,
        "map_score": round(map_score, 3),
        "reasons": d.reasons,
        "message": d.message,
    }
    log_event("decide", {"decision": d.kind, "step_id": d.step_id})
    return out


@app.post("/emit")
def api_emit(body: DecideIn) -> dict[str, Any]:
    steps = _steps or _load()
    order = WorkOrder(id="WO-api", completed=set(body.completed))
    ctx = ShopContext(hands_clear=body.hands_clear)
    step_id = body.step_id
    if not step_id and body.action:
        step_id, _ = map_action_to_step(body.action, steps)
    step = steps.get(step_id) if step_id else None
    if body.step_id and step is None:
        raise HTTPException(status_code=404, detail=f"unknown step: {body.step_id}")
    d = decide(step, order, ctx, raw_action=body.action)
    payload = to_ros_fields(from_decision(d))
    log_event("emit", {"decision": d.kind, "step_id": d.step_id})
    return payload


@app.post("/next")
def api_next(body: NextIn) -> dict[str, Any]:
    steps = _steps or _load()
    order = WorkOrder(id="WO-api", completed=set(body.completed))
    ctx = ShopContext(hands_clear=body.hands_clear)
    ready = ready_steps(steps, order, ctx)
    return {"ready": ready, "titles": {sid: steps[sid].title for sid in ready}}
