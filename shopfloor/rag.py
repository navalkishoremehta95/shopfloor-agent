"""Hybrid SOP retrieve with citations and a small eval harness."""

from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import _tokens


@dataclass
class Hit:
    step_id: str
    score: float
    lexical: float
    dense: float
    title: str
    citation: str
    body: str


def _citation(body: str, max_len: int = 160) -> str:
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if not lines:
        return ""
    # skip the "## STEP-xx title" head; prefer the first detail line
    text = lines[1] if len(lines) > 1 else lines[0]
    text = re.sub(r"\s+", " ", text)
    if len(text) > max_len:
        return text[: max_len - 1].rstrip() + "…"
    return text


def _ngrams(text: str, n: int = 3) -> set[str]:
    s = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) < n:
        return {s} if s else set()
    return {s[i : i + n] for i in range(len(s) - n + 1)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _lexical(query: str, head: str, body: str) -> float:
    q = _tokens(query)
    if not q:
        return 0.0
    body_toks = _tokens(body)
    head_toks = _tokens(head)
    overlap = q & body_toks
    if not overlap:
        return 0.0
    score = len(overlap) / len(q)
    title_hits = q & head_toks
    if title_hits:
        score = min(1.0, score + 0.2 * len(title_hits) / len(q))
    return score


def _local_dense(query: str, body: str) -> float:
    return _jaccard(_ngrams(query), _ngrams(body))


def _openai_dense_scores(query: str, bodies: list[str]) -> list[float] | None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None

    client = OpenAI(api_key=api_key)
    model = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    inputs = [query, *bodies]
    resp = client.embeddings.create(model=model, input=inputs)
    vectors = [item.embedding for item in sorted(resp.data, key=lambda d: d.index)]
    qv = vectors[0]

    def cos(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    return [cos(qv, v) for v in vectors[1:]]


def _sections(path: Path) -> list[tuple[str, str, str]]:
    text = path.read_text(encoding="utf-8")
    out: list[tuple[str, str, str]] = []
    for block in text.split("## ")[1:]:
        body = block.strip()
        if not body:
            continue
        head = body.splitlines()[0].strip()
        step_id = head.split()[0] if head else "?"
        out.append((step_id, head, body))
    return out


def hybrid_retrieve(
    path: str | Path,
    query: str,
    top_k: int = 3,
    min_score: float = 0.0,
    *,
    lexical_weight: float = 0.65,
    use_embeddings: bool = True,
) -> list[Hit]:
    """Lexical + dense hybrid rank. Dense uses OpenAI embeddings if keyed, else char n-grams."""
    path = Path(path)
    sections = _sections(path)
    if not sections or not query.strip():
        return []

    bodies = [body for _, _, body in sections]
    embed_scores = _openai_dense_scores(query, bodies) if use_embeddings else None

    hits: list[Hit] = []
    for i, (step_id, head, body) in enumerate(sections):
        lex = _lexical(query, head, body)
        if embed_scores is not None:
            dense = max(0.0, float(embed_scores[i]))
        else:
            dense = _local_dense(query, body)
        if lex <= 0 and dense <= 0:
            continue
        score = lexical_weight * lex + (1.0 - lexical_weight) * dense
        if score < min_score:
            continue
        hits.append(
            Hit(
                step_id=step_id,
                score=score,
                lexical=lex,
                dense=dense,
                title=head,
                citation=_citation(body),
                body=body,
            )
        )

    hits.sort(key=lambda h: (-h.score, h.step_id))
    return hits[:top_k]


def hits_as_dicts(hits: list[Hit]) -> list[dict[str, Any]]:
    return [
        {
            "step_id": h.step_id,
            "score": round(h.score, 3),
            "lexical": round(h.lexical, 3),
            "dense": round(h.dense, 3),
            "title": h.title,
            "citation": h.citation,
        }
        for h in hits
    ]


def eval_retrieve(
    sop_path: str | Path,
    cases_path: str | Path,
    *,
    top_k: int = 3,
) -> dict[str, Any]:
    cases = json.loads(Path(cases_path).read_text(encoding="utf-8"))["cases"]
    hit1 = 0
    hitk = 0
    rows: list[dict[str, Any]] = []
    for case in cases:
        hits = hybrid_retrieve(sop_path, case["query"], top_k=top_k, use_embeddings=False)
        ranked = [h.step_id for h in hits]
        expect = set(case["expect"])
        ok1 = bool(ranked) and ranked[0] in expect
        okk = bool(expect & set(ranked))
        hit1 += int(ok1)
        hitk += int(okk)
        rows.append(
            {
                "id": case.get("id", case["query"][:40]),
                "query": case["query"],
                "expect": case["expect"],
                "got": ranked,
                "hit_at_1": ok1,
                "hit_at_k": okk,
            }
        )
    n = len(cases) or 1
    return {
        "n": len(cases),
        "hit_at_1": round(hit1 / n, 3),
        "hit_at_k": round(hitk / n, 3),
        "cases": rows,
    }
