# ShopFloor Agent — roadmap

Procedure-compliant assembly assistant, built notebook by notebook.
SOP and evaluation are grounded in **MIAM / M³-HRC** industrial assembly research.

```
Rules → State → Safety → Query → Retrieval → Agent
         (C)     (HRC)    (API)     (RAG)      (LLM)
```

## Parts

| Part | Notebook section | Goal | Status |
|------|------------------|------|--------|
| 1 | `01_sop_graph` — graph | DAG, $\mathrm{Pred}(s)$, allow rule | done |
| 2 | `01_sop_graph` — parser | Load `miam_assembly_subset.md`, update $C$ | done |
| 3 | `02_risk_gate` | Risk gate: `hands_clear` for high-risk steps | done |
| 4 | you write | `can_start(step_id)` → allowed + reasons | planned |
| 5 | you write | Load M³-HRC `c1_action_annotations.csv` (local only) | planned |
| 6 | you write | Replay session vs SOP compliance | planned |
| 7 | you write | Retrieve SOP snippets (simple search) | planned |
| 8 | you write | LLM calls tools (`check_order`, `check_safety`) | planned |
| 9 | you write | FastAPI or CLI + Docker (optional) | planned |
| 10 | you write | GitHub Actions / tests (optional) | planned |

## Data policy (M³-HRC)

- Request access: [Hugging Face dataset](https://huggingface.co/datasets/ArvindSihag/M3_Multimodal_Human_Robot_Collaboration_Dataset)
- License: **CC BY-NC 4.0** — research use, cite, no redistribution
- Keep downloads in `data/` (gitignored) — never commit videos, IMU, or CSVs
- The repo ships a **derived SOP markdown subset** only, not raw dataset files

## Citation

```bibtex
@inproceedings{arvind2026action,
  title={The Action-Engagement-Collaboration Triad: A Multimodal Analytical Framework for Human-Robot Collaboration},
  author={Arvind and Mehta, Naval Kishore and Kumar, Himanshu and Saurav, Sumeet and Singh, Sanjay},
  booktitle={HRI}, year={2026}
}
```

## Part 3 hint (your turn)

Extend allow rule:

$$\text{allowed}(s) \iff \mathrm{Pred}(s) \subseteq C \land (\text{risk}(s) \neq \text{high} \lor H)$$

where $H$ = hands clear. STEP-06 in the MIAM subset is marked high risk.
