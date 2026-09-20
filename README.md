# ShopFloor Agent

Procedure-compliant assembly assistant for MIAM / M3-HRC workflows.

See [ROADMAP.md](ROADMAP.md).

## Layout

```
shopfloor/         # parse_sop, can_start, retrieve
notebooks/
docs/sop_samples/
tests/
```

## Notebooks

| Notebook | Focus |
|----------|--------|
| `notebooks/01_sop_graph.ipynb` | SOP DAG + parser |
| `notebooks/02_checks.ipynb` | Order + risk gate (`can_start`) |
| `notebooks/03_retrieve.ipynb` | SOP snippet retrieval |

## Setup

```bash
pip install -r requirements.txt
python -m pytest -q
```

## Author

Naval Kishore Mehta

## License

MIT (code). M3-HRC dataset: CC BY-NC 4.0.
