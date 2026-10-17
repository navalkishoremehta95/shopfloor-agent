"""Convert one Assembly101 mistake-detection CSV into a shopfloor session.

Source annotations:
https://github.com/assembly-101/assembly101-mistake-detection (CC BY-NC 4.0)

Usage:
  python scripts/import_assembly101.py data/external/assembly101_9033_c02a.csv \\
      -o docs/sessions/assembly101_9033_c02a.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def convert(src: Path, fps: float = 30.0) -> list[dict[str, str]]:
    rows_out: list[dict[str, str]] = []
    with src.open(encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        for row in reader:
            if len(row) < 6:
                continue
            start, _end, verb, this, that, label = row[:6]
            verb = verb.strip().lower()
            # attach-only: detach/correction rows confuse step mapping
            if verb != "attach":
                continue
            try:
                t = float(start) / fps
            except ValueError:
                continue
            action = f"{verb} {this.strip()} {that.strip()}"
            hands = "false" if ("arm" in action and "boom" in action and label != "correct") else "true"
            rows_out.append(
                {
                    "t": f"{t:.2f}",
                    "action": action,
                    "hands_clear": hands,
                    "src_label": label.strip(),
                }
            )
    return rows_out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("src", type=Path)
    p.add_argument("-o", "--out", type=Path, required=True)
    p.add_argument("--fps", type=float, default=30.0)
    args = p.parse_args()
    rows = convert(args.src, fps=args.fps)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["t", "action", "hands_clear", "src_label"])
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} events -> {args.out}")


if __name__ == "__main__":
    main()
