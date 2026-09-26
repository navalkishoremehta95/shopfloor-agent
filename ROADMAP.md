# ShopFloor Agent — roadmap

SOP grounded in MIAM / M³-HRC.

```
Rules → State → Safety → Query → Retrieval → Replay → Tools → CLI
```

## Status

| Piece | Goal | Status |
|-------|------|--------|
| `shopfloor_agent.ipynb` | Order + risk gate + retrieve | done |
| `docs/sessions/` | Sample labeled timeline | done |
| `shopfloor/replay.py` | Replay session vs SOP | done |
| `shopfloor/tools.py` | `check_can_start` / `retrieve_sop` tools | done |
| `python -m shopfloor` | CLI (`check`, `retrieve`, `replay`) | done |
| — | Swap sample for real M³-HRC export under `data/` | optional |
| — | FastAPI wrapper | optional |

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
