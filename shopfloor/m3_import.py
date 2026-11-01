"""Local M3-HRC annotations -> session CSV. Does not download anything."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


_ACTION_KEYS = ("action", "label", "Action", "primitive", "category")
_START_KEYS = ("start", "t_start", "temporal_segment_start", "t")


def action_from_name(name: str) -> str:
    """`01_take_rpi_CM.mp4` -> `take rpi CM`."""
    stem = Path(name).stem
    stem = re.sub(r"^clip_", "", stem, flags=re.IGNORECASE)
    stem = re.sub(r"_rgb$", "", stem, flags=re.IGNORECASE)
    stem = re.sub(r"^\d+_", "", stem)
    return stem.replace("_", " ").strip()


def _obj(text: str | None) -> dict:
    raw = (text or "").strip()
    if not raw:
        return {}
    try:
        val = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return val if isinstance(val, dict) else {}


def _action(meta: dict, filename: str) -> str:
    for key in _ACTION_KEYS:
        if meta.get(key):
            return str(meta[key]).replace("_", " ").strip()
    return action_from_name(filename)


def _start(shape: dict, meta: dict, fallback: float) -> float:
    for src in (shape, meta):
        for key in _START_KEYS:
            if src.get(key) not in (None, ""):
                return float(src[key])
    return fallback


def _hands(meta: dict) -> str:
    if "hands_clear" in meta:
        val = str(meta["hands_clear"]).strip().lower()
        return "false" if val in {"0", "false", "no", "n"} else "true"
    return "true"


def _read_csv(path: Path) -> list[dict[str, str]]:
    lines = [
        ln
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.lstrip().startswith("#")
    ]
    if not lines:
        return []
    return list(csv.DictReader(lines))


def events_from_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    for i, row in enumerate(rows):
        filename = (row.get("filename") or row.get("file") or "").strip()
        meta = _obj(row.get("region_attributes") or row.get("metadata") or row.get("file_attributes"))
        # file_attributes is often empty {}; prefer region metadata for the label
        if not any(meta.get(k) for k in _ACTION_KEYS):
            meta = {**_obj(row.get("file_attributes")), **meta}
        shape = _obj(row.get("region_shape_attributes"))
        if row.get("temporal_segment_start"):
            shape = {**shape, "start": row["temporal_segment_start"]}
        if row.get("action") or row.get("label"):
            meta = {**meta, "action": row.get("action") or row.get("label")}
        if row.get("hands_clear"):
            meta = {**meta, "hands_clear": row["hands_clear"]}

        action = _action(meta, filename)
        if not action:
            continue
        t = _start(shape, meta, float(i))
        if row.get("t") not in (None, ""):
            t = float(row["t"])
        events.append({"t": f"{t:.2f}", "action": action, "hands_clear": _hands(meta)})

    events.sort(key=lambda e: float(e["t"]))
    return events


def events_from_clips(folder: Path) -> list[dict[str, str]]:
    clips = sorted(
        p
        for p in folder.iterdir()
        if p.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"}
    )
    events: list[dict[str, str]] = []
    for i, clip in enumerate(clips):
        action = action_from_name(clip.name)
        if not action:
            continue
        events.append({"t": f"{float(i):.2f}", "action": action, "hands_clear": "true"})
    return events


def load_m3_events(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    if path.is_dir():
        ann = path / "c1_action_annotations.csv"
        if ann.is_file():
            return events_from_rows(_read_csv(ann))
        clips = path / "c1_clips"
        if clips.is_dir():
            return events_from_clips(clips)
        raise FileNotFoundError(
            f"no c1_action_annotations.csv or c1_clips/ under {path}"
        )
    if not path.is_file():
        raise FileNotFoundError(path)
    return events_from_rows(_read_csv(path))


def write_session(events: list[dict[str, str]], out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["t", "action", "hands_clear"])
        writer.writeheader()
        writer.writerows(events)
    return out
