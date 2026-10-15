# ShopFloor Agent — roadmap

SOP grounded in MIAM / M³-HRC.

```
Rules → Safety → Retrieve → Map → Decide → Replay → CLI
```

## Status

| Piece | Goal | Status |
|-------|------|--------|
| `shopfloor_agent.ipynb` | Order, safety, retrieve, decide, replay | done |
| `docs/sessions/` | Step-id and action-label samples | done |
| `shopfloor/map_actions.py` | Action label → STEP id | done |
| `shopfloor/decide.py` | ACT / WAIT / GUIDE | done |
| `shopfloor/replay.py` | Session replay report | done |
| `python -m shopfloor` | check, retrieve, decide, next, replay | done |
| `shopfloor/next.py` | Ready steps under current state | done |
| CSV sessions | `docs/sessions/*.csv` load path | done |
| `shopfloor/agent.py` | Optional OpenAI tool loop (`ask`) | done |
| `shopfloor/rag.py` | Hybrid retrieve + citations + eval | done |
| — | Real M³-HRC labels under `data/` | next |
| — | ROS 2 / FastAPI bridge | later |

## Data

- [M³-HRC on Hugging Face](https://huggingface.co/datasets/ArvindSihag/M3_Multimodal_Human_Robot_Collaboration_Dataset) (CC BY-NC 4.0)
- Keep downloads in `data/` (gitignored)
- Repo ships derived SOP markdown + a small sample session JSON

## Citation

```bibtex
@inproceedings{arvind2026action,
  title={The Action-Engagement-Collaboration Triad: A Multimodal Analytical Framework for Human-Robot Collaboration},
  author={Arvind and Mehta, Naval Kishore and Kumar, Himanshu and Saurav, Sumeet and Singh, Sanjay},
  booktitle={HRI}, year={2026}
}
```
