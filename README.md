# ShopFloor Agent

Procedure-compliant assembly assistant for MIAM / M3-HRC workflows.

See [ROADMAP.md](ROADMAP.md).

## Layout

```
shopfloor/         # parse_sop, can_start, retrieve
notebooks/shopfloor_agent.ipynb
docs/sop_samples/
tests/
```

## Notebook

[`notebooks/shopfloor_agent.ipynb`](notebooks/shopfloor_agent.ipynb) — order, safety, retrieve, next steps.

## Setup

```bash
pip install -r requirements.txt
python -m pytest -q
jupyter notebook notebooks/shopfloor_agent.ipynb
```

## Author

Naval Kishore Mehta

## License

MIT (code). M3-HRC dataset: CC BY-NC 4.0.
