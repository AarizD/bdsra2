# Prompt Injection and Poisoned Documents in RAG Ingestion

This project evaluates ingestion-time defenses against indirect prompt injection using the **public datasets specified for Project Topic 38**. The default pipeline downloads actual benchmark records and real Wikimedia articles; it does not generate a synthetic corpus and does not fall back to fabricated records when a source is unavailable.

## Public datasets

| Dataset | Role in this project |
|---|---|
| Wikimedia Wikipedia (`wikimedia/wikipedia`, `20231101.en`) | Clean real-document corpus and benign false-positive evaluation |
| deepset prompt-injections (`deepset/prompt-injections`) | Labeled injection and benign examples for scanner training/testing |
| BIPIA (`geodesic-research/bipia` public mirror) | Poisoned contexts, paired questions, and held-out attack-success evaluation |
| Tensor Trust (`qxcv/tensor-trust` mirror) | Human-authored prompt-injection examples for scanner evaluation |

The downloader records exact IDs, counts, splits, and license notes in `data/attacks/DATASET_MANIFEST.json`. It omits Tensor Trust `access_code` fields and redacts occurrences in the prompt text. The Tensor Trust mirror has no license metadata in its dataset card; check upstream terms before redistributing its content. Wikipedia and BIPIA records carry their respective attribution/share-alike requirements.

## Run the project

Requires Python 3.10+ and internet access for initial dataset downloads.

```bash
python -m venv .venv
# Activate the environment, then:
python -m pip install -e ".[dev]"
python scripts/run_public_pipeline.py  # Download data, evaluate, generate graphs/report
python -m pip install -e ".[video]"   # One-time install for the explainer video
python scripts/generate_project_video.py
python -m pytest -q                  # Run unit and regression tests
```

The equivalent Make targets are `make data` and `make all` (GNU Make / Git Bash / WSL). Sampling can be adjusted without editing code:

```bash
# Example: 2,000 Wikipedia articles; at most 600 rows per injection source
python scripts/run_public_pipeline.py --wikipedia-size 2000 --per-attack-source 600
```

`make smoke` uses smaller public-data samples; it still downloads real data and has no synthetic fallback. Public benchmark artifacts are stored locally under `data/` and generated outputs under `results/` and `reports/`.

## Evaluation and interpretation

- D1 is the explainable content-rule scanner; D2 is a word/character TF-IDF classifier. Exact normalized duplicate groups are assigned together to deterministic 60/20/20 train/dev/test partitions. Thresholds maximize dev recall subject to a declared 5% FPR ceiling overall and within each benign source.
- The report includes pooled and per-source confusion counts, Wilson confidence intervals, test-only precision-recall curves, source-held-out generalization (BIPIA and Tensor Trust), paired-context retrieval Recall@k/MRR, and a crowd-authored SQuAD validation QA evaluation with gold-span evidence coverage.
- `data/clean/squad_qa.jsonl` and `squad_contexts.jsonl` hold 1,200 crowd-authored SQuAD validation QA pairs and their passages. The report measures gold-context retrieval and gold-answer evidence; the optional simulator EM/F1 remains explicitly non-model diagnostic output.
- The default retriever is BM25, selected by maximizing paired-context Recall@5 on BIPIA dev among feature hashing, word/character TF-IDF, BM25, and reciprocal-rank-fusion hybrid (BM25 + word TF-IDF). Clean-title utility and the sealed test candidate comparison are reported separately and do not change selection.
- The deterministic victim output is reported only as a **simulator diagnostic, not ASR**. No real-model endpoint is contacted by the default pipeline. A real-model ASR claim requires an explicitly identified/authorized model, fixed settings, a benchmark-aligned scoring rule, clean controls, and repeated trials.
- Provenance, quarantine, context-hardening, and output-guard implementations remain available in `src/ragdef/defenses/`; the public benchmark report identifies which scanner defenses are quantitatively evaluated.
- Cost figures are scenario estimates using the assumptions in `configs/default.yaml`, not observed expenses.
- Dataset reuse/redistribution findings are recorded in `DATA_RIGHTS_AUDIT.md`. In particular, Tensor Trust redistribution rights remain unresolved; keep those fetched records local/private until an explicit license or written permission is obtained.

## Outputs

| Deliverable | Location |
|---|---|
| Public attack and benign datasets | `data/attacks/` |
| Dataset source manifest and sample counts | `data/attacks/DATASET_MANIFEST.json` |
| Defense code | `src/ragdef/defenses/` |
| Evaluation tables | `results/tables/public_*.csv` |
| Clean utility and retriever comparison | `results/tables/public_clean_utility.csv`, `public_retriever_selection.csv`, `public_retriever_test_comparison.csv` |
| Crowd-authored clean QA utility | `results/tables/public_squad_clean_qa.csv` |
| Source-heldout scanner metrics | `results/tables/public_source_holdout_metrics.csv` |
| Generated graphs | `results/figures/public_*.png` |
| Effectiveness report | `reports/effectiveness_report.md` |
| Project explainer video | `project_overview.mp4` |

All attack text is benchmark content; it is never executed as code or sent to real external destinations. Results are limited by dataset selection, source/task distribution, the simulated victim, and the cost assumptions. A low error rate on these benchmarks is not a deployment security guarantee.
