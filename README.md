# ShopFloor Agent

Procedure-compliant assembly assistant for MIAM / M3-HRC workflows.

See [ROADMAP.md](ROADMAP.md).

## System Architecture

The ShopFloor Agent is designed as a high-level reasoning and coordination
layer for human–cobot collaboration. It combines human activity recognition,
task-state tracking, SOP knowledge, safety constraints, and LLM-based reasoning
to determine whether the cobot should act, wait, or provide guidance.
Robot commands are executed through ROS 2 and the robot motion-planning stack.

```mermaid
flowchart TD

    A["RGB / RGB-D / IMU / Robot State"]
    B["Action Recognition"]
    C["Human + Task State Tracker"]

    subgraph AGENT["ShopFloor Agent"]
        D["SOP + Task Graph"]
        E["Safety Rules"]
        F["LLM Reasoning"]
    end

    G{"Decision"}
    H["WAIT"]
    I["ROBOT ACTION"]
    N["GUIDE HUMAN"]
    J["ROS 2"]
    K["Motion Planner / MoveIt"]
    L["Cobot"]
    M["Observe Result"]

    A --> B
    B --> C
    C --> D

    D --> E
    E --> F
    F --> G

    G -->|Human action incomplete| H
    G -->|Safe + Step Ready| I
    G -->|Operator needs guidance| N

    H --> M
    N --> M

    I --> J
    J --> K
    K --> L
    L --> M

    M --> B
```

## Layout

```
shopfloor/           # parse, can_start, retrieve, map, decide, replay, CLI
notebooks/shopfloor_agent.ipynb
docs/sop_samples/
docs/sessions/
tests/
```

## Setup

```bash
pip install -r requirements.txt
python -m pytest -q
jupyter notebook notebooks/shopfloor_agent.ipynb
```

## CLI

```bash
python -m shopfloor check STEP-06 --done STEP-01,STEP-02,STEP-03,STEP-04,STEP-05 --hands-clear
python -m shopfloor retrieve "high risk fastening"
python -m shopfloor eval-retrieve
python -m shopfloor decide --action "screw screw with screwdriver" --done STEP-01,STEP-02,STEP-03,STEP-04,STEP-05 --hands-clear
python -m shopfloor next --done STEP-01,STEP-02,STEP-03,STEP-04 --hands-clear
python -m shopfloor replay docs/sessions/session_m3_actions.csv
set OPENAI_API_KEY=...
python -m shopfloor ask "Can STEP-06 start if STEP-01..05 are done and hands are clear?"
```

## Authors

Naval Kishore Mehta · [Arvind](https://github.com/arvindsihag)

## License

MIT (code). M3-HRC dataset: CC BY-NC 4.0.
