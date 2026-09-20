# ShopFloor Agent — roadmap

Built notebook by notebook. SOP grounded in MIAM / M³-HRC.

```
Rules → State → Safety → Query → Retrieval → Agent
```

## Parts

| Part | Notebook | Goal | Status |
|------|----------|------|--------|
| 1–2 | `01_sop_graph` | DAG + parse MIAM subset | done |
| 3–4 | `02_checks` | Risk gate + `can_start` reasons | done |
| 5 | — | Load local M³-HRC annotations | planned |
| 6 | — | Replay session vs SOP | planned |
| 7 | `03_retrieve` | Retrieve SOP snippets | done |
| 8 | — | LLM tools (`check_order`, `check_safety`) | planned |
| 9 | — | FastAPI / CLI (optional) | planned |

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
