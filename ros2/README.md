# ROS 2 bridge (stub)

ShopFloor Agent publishes **ACT / WAIT / GUIDE** as JSON on `/shopfloor/command`.
Perception / task state should publish observations to `/shopfloor/observation`.

This folder is an interface sketch. Install ROS 2 and `rclpy` on the robot PC when
you wire a real cell; the core library does not depend on ROS.

Suggested flow:

```
/shopfloor/observation  →  shopfloor.decide  →  /shopfloor/command  →  MoveIt / operator UI
```

Payload shape: see `shopfloor/bridge.py` (`to_ros_fields`).

Dry-run without ROS:

```bash
python -m shopfloor emit --action "screw screw with screwdriver" --done STEP-01,STEP-02,STEP-03,STEP-04,STEP-05 --hands-clear
```
