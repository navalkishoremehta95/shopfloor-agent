"""Optional rclpy node. Run only where ROS 2 is installed.

  ros2 run ...  (or)  python ros2/shopfloor_bridge_node.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shopfloor import ShopContext, WorkOrder, parse_sop
from shopfloor.bridge import from_decision, to_ros_fields
from shopfloor.decide import decide
from shopfloor.map_actions import map_action_to_step


def main() -> None:
    try:
        import rclpy
        from rclpy.node import Node
        from std_msgs.msg import String
    except ImportError as exc:
        raise SystemExit(
            "rclpy not installed. Use: python -m shopfloor emit ... for a dry-run."
        ) from exc

    sop = ROOT / "docs" / "sop_samples" / "miam_assembly_subset.md"
    steps = parse_sop(sop)

    class Bridge(Node):
        def __init__(self) -> None:
            super().__init__("shopfloor_bridge")
            self._pub = self.create_publisher(String, "/shopfloor/command", 10)
            self.create_subscription(
                String, "/shopfloor/observation", self._on_obs, 10
            )
            self.get_logger().info("shopfloor_bridge ready")

        def _on_obs(self, msg: String) -> None:
            data = json.loads(msg.data)
            completed = set(data.get("completed") or [])
            hands = bool(data.get("hands_clear", False))
            action = data.get("action")
            step_id = data.get("step_id")
            order = WorkOrder(id="WO-ros", completed=completed)
            ctx = ShopContext(hands_clear=hands)
            if not step_id and action:
                step_id, _ = map_action_to_step(str(action), steps)
            step = steps.get(step_id) if step_id else None
            cmd = from_decision(decide(step, order, ctx, raw_action=action))
            out = String()
            out.data = json.dumps(to_ros_fields(cmd))
            self._pub.publish(out)

    rclpy.init()
    node = Bridge()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
