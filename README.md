# ShopFloor Agent

Procedure-compliant assembly assistant for MIAM / M3-HRC workflows.

See [ROADMAP.md](ROADMAP.md).

## Layout

```
shopfloor/           # parse, can_start, retrieve, replay, tools, CLI
notebooks/shopfloor_agent.ipynb
docs/sop_samples/
docs/sessions/       # sample timelines (derived, not raw dataset)
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
python -m shopfloor replay docs/sessions/sample_miam_subset.json
```

## Author

Naval Kishore Mehta

## License

MIT (code). M3-HRC dataset: CC BY-NC 4.0.
