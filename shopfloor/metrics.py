"""Append-only JSONL metrics (local)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG = ROOT / "data" / "metrics.jsonl"


def log_event(kind: str, payload: dict[str, Any], path: Path | None = None) -> None:
    log_path = path or Path(os.environ.get("SHOPFLOOR_METRICS", DEFAULT_LOG))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        **payload,
    }
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
