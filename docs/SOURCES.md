# Data sources

- MIAM / M3-HRC: https://huggingface.co/datasets/ArvindSihag/M3_Multimodal_Human_Robot_Collaboration_Dataset (CC BY-NC 4.0; gated; do not redistribute). Extract a session under `data/`, then `python -m shopfloor import-m3 data/<session> -o data/sessions/<session>.csv`.
- Assembly101 mistake annotations: https://github.com/assembly-101/assembly101-mistake-detection (CC BY-NC 4.0). Derived session: `docs/sessions/assembly101_9033_c02a.csv`.
