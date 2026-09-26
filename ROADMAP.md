# ShopFloor Agent — roadmap

Built notebook by notebook. SOP grounded in MIAM / M³-HRC.

```
Rules → State → Safety → Query → Retrieval → Agent
```

## Status

| Piece | Goal | Status |
|-------|------|--------|
| `shopfloor_agent.ipynb` | Order + risk gate + retrieve | done |
| — | Load local M³-HRC annotations | planned |
| — | Replay session vs SOP | planned |
| — | LLM tools (`check_order`, `check_safety`) | planned |
| — | FastAPI / CLI (optional) | planned |

## Data

- [M³-HRC on Hugging Face](https://huggingface.co/datasets/ArvindSihag/M3_Multimodal_Human_Robot_Collaboration_Dataset) (CC BY-NC 4.0)
- Keep downloads in `data/` (gitignored)
- Repo ships derived SOP markdown only

## Citation

```bibtex
@inproceedings{arvind2026action,
  title={The Action-Engagement-Collaboration Triad: A Multimodal Analytical Framework for Human-Robot Collaboration},
  author={Arvind and Mehta, Naval Kishore and Kumar, Himanshu and Saurav, Sumeet and Singh, Sanjay},
  booktitle={HRI}, year={2026}
}
```
