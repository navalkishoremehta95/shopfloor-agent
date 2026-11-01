"""Convert one local M³-HRC session into a shopfloor CSV.

The Hugging Face set is gated. Point this at an extracted session folder
(or at c1_action_annotations.csv). Output stays under data/ unless you
pass -o somewhere else. Do not commit the raw download.

Usage:
  python scripts/import_m3hrc.py data/2024-9-20_11-40-54-563 \\
      -o data/sessions/m3_2024-9-20.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shopfloor.m3_import import load_m3_events, write_session  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("src", type=Path, help="session dir or c1_action_annotations.csv")
    p.add_argument("-o", "--out", type=Path, required=True)
    args = p.parse_args()
    events = load_m3_events(args.src)
    write_session(events, args.out)
    print(f"wrote {len(events)} events -> {args.out}")


if __name__ == "__main__":
    main()
