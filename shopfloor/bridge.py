"""Execution bridge payload (ROS 2–ready, no rclpy required)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .decide import Decision


@dataclass
class Command:
    """What a motion / operator stack should consume."""

    decision: str  # ACT | WAIT | GUIDE
    step_id: str | None
    message: str
    reasons: list[str]
    frame_id: str = "shopfloor"
    # suggested topics when wiring ROS 2
    topic_command: str = "/shopfloor/command"
    topic_feedback: str = "/shopfloor/observation"


def from_decision(d: Decision, *, frame_id: str = "shopfloor") -> Command:
    return Command(
        decision=d.kind,
        step_id=d.step_id,
        message=d.message,
        reasons=list(d.reasons),
        frame_id=frame_id,
    )


def to_dict(cmd: Command) -> dict[str, Any]:
    return asdict(cmd)


def to_ros_fields(cmd: Command) -> dict[str, Any]:
    """Flat fields suitable for a std_msgs/String JSON or custom msg."""
    return {
        "frame_id": cmd.frame_id,
        "decision": cmd.decision,
        "step_id": cmd.step_id or "",
        "message": cmd.message,
        "reasons": ",".join(cmd.reasons),
        "command_topic": cmd.topic_command,
        "feedback_topic": cmd.topic_feedback,
    }
