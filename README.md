# ShopFloor Agent

Procedure-compliant assembly assistant (notebooks + small Python helpers).

Grounded in MIAM / M3-HRC industrial assembly (FRAS kit). See [ROADMAP.md](ROADMAP.md).

## Layout

```
shopfloor/          # Step, WorkOrder, parse_sop, can_start
notebooks/          # learning notebooks
docs/sop_samples/   # toy + MIAM subset SOPs
tests/              # basic checks
```

## Notebooks

- [notebooks/01_sop_graph.ipynb](notebooks/01_sop_graph.ipynb) — Parts 1–2: graph + load SOP
- [notebooks/02_risk_gate.ipynb](notebooks/02_risk_gate.ipynb) — Part 3: hands_clear for high-risk steps
- [docs/sop_samples/miam_assembly_subset.md](docs/sop_samples/miam_assembly_subset.md)

## Setup

```bash
pip install -r requirements.txt
jupyter notebook notebooks/01_sop_graph.ipynb
```

Open cells top to bottom (Shift+Enter). For Part 3, start Jupyter from the repo root so `shopfloor` imports cleanly.

```bash
python -m pytest -q
```

## Author

Naval Kishore Mehta

## License

MIT (code). M3-HRC dataset: CC BY-NC 4.0 — see dataset page.
