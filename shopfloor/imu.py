"""Wrist IMU window. Same columns as preprocess/sync_C1_IMU.py."""

from __future__ import annotations

import csv
import math
from pathlib import Path

# crop_imu_data uses a 5s lookback
WINDOW_S = 5.0
# still bench vs fastening, from a few clips
ACCEL_STD = 0.08
GYRO_MEAN = 20.0

LEFT = "cc:59:6a:eb:08:f5"   # lh
RIGHT = "d3:a2:b7:99:b3:53"  # rh


def _num(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _mag(x, y, z):
    return math.sqrt(x * x + y * y + z * z)


def load_csv(path, hand=None):
    want = {"left": LEFT, "right": RIGHT}.get(hand)
    rows = []
    with Path(path).open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            dev = (row.get("Device name") or "").strip().lower()
            if want and dev and dev != want:
                continue
            t = _num(row.get("relative_time") or row.get("t"))
            ax = _num(row.get("Acceleration X(g)"))
            ay = _num(row.get("Acceleration Y(g)"))
            az = _num(row.get("Acceleration Z(g)"))
            if t is None or ax is None or ay is None or az is None:
                continue
            item = {"t": t, "a": _mag(ax, ay, az)}
            gx = _num(row.get("Angular velocity X(°/s)"))
            gy = _num(row.get("Angular velocity Y(°/s)"))
            gz = _num(row.get("Angular velocity Z(°/s)"))
            if None not in (gx, gy, gz):
                item["g"] = _mag(gx, gy, gz)
            rows.append(item)
    rows.sort(key=lambda r: r["t"])
    return rows


def _std(vals):
    n = len(vals)
    if n < 2:
        return 0.0
    mean = sum(vals) / n
    return math.sqrt(sum((v - mean) ** 2 for v in vals) / (n - 1))


def window_stats(rows, t, window=WINDOW_S):
    chunk = [r for r in rows if t - window < r["t"] <= t]
    accel = [r["a"] for r in chunk]
    gyro = [r["g"] for r in chunk if "g" in r]
    accel_std = round(_std(accel), 4) if accel else None
    gyro_mean = round(sum(gyro) / len(gyro), 3) if gyro else None
    if not chunk:
        moving = None
    else:
        moving = (accel_std or 0) >= ACCEL_STD or (gyro_mean or 0) >= GYRO_MEAN
    clear = None if moving is None else (not moving)
    return {
        "t": t,
        "window_s": window,
        "n": len(chunk),
        "accel_std_g": accel_std,
        "gyro_mean_dps": gyro_mean,
        "moving": moving,
        "hands_clear": clear,
    }


def hands_window(left=None, right=None, t=0.0, window=WINDOW_S):
    hands = {}
    if left:
        hands["left"] = window_stats(load_csv(left, "left"), t, window)
    if right:
        hands["right"] = window_stats(load_csv(right, "right"), t, window)
    if not hands:
        raise FileNotFoundError("need lh or rh csv")
    flags = [h["moving"] for h in hands.values() if h["moving"] is not None]
    moving = any(flags) if flags else None
    return {
        "t": t,
        "window_s": window,
        "hands": hands,
        "moving": moving,
        "hands_clear": None if moving is None else (not moving),
    }
