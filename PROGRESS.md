# Progress

- [x] Replace synthetic corpus/attack generation with the Topic 38 public sources.
- [x] Download and normalize Wikimedia, deepset prompt-injections, BIPIA, and Tensor Trust records.
- [x] Preserve dataset source/split metadata and redact Tensor Trust access codes.
- [x] Prepare full-size public-data samples and apply deterministic grouped 60/20/20 deduplication splits.
- [x] Train scanners on train only; select scanner thresholds and the retriever on dev only.
- [x] Implement sealed held-out scanner metrics, per-source confidence intervals, PR curves, retrieval Recall@k/MRR, simulator-only diagnostics, and low/base/high cost sensitivity.
- [x] Add regression coverage for grouped splits, conflict exclusion, pooled/source FPR constraints, undefined single-class metrics, and zero-event intervals.
- [x] Run the full regression suite (34 passed) and Ruff (clean).
- [x] Regenerate final benchmark artifacts after the latest proxy top-5 scoring, query alignment, and confidence-interval fixes.
- [x] Regenerate the explainer video from the final report and outputs.
- [x] Record final output status and remaining limitations below.
- [x] Add a source-held-out BIPIA/Tensor Trust generalization evaluation, withholding all duplicate aliases from fitting/tuning.
- [x] Add held-out clean Wikipedia title-query retrieval and deterministic extractive answer-utility metrics under the defense policies.
- [x] Compare hashing, word TF-IDF, and character TF-IDF on dev and report sealed BIPIA/clean test comparisons without test-driven selection.
- [x] Audit Tensor Trust reuse/redistribution evidence and document the unresolved-license restriction.
- [x] Regenerate the final benchmark report/tables/figures with sealed retriever candidate comparison; run the final full suite.
- [x] Regenerate the 78-second overview video with the final source-heldout and clean-utility results.
- [x] Add BM25 and a BM25 + word-TF-IDF reciprocal-rank-fusion hybrid with pipeline regression tests.
- [x] Expand dev-only selection and sealed test comparisons to include BM25 and hybrid retrieval.
- [x] Run the expanded full test suite (37 passed).
- [x] Regenerate the full benchmark outputs with BM25/hybrid candidate evaluation and run final checks.
- [x] Regenerate the 78-second overview video with BM25 as the selected retriever.
- [x] Add SQuAD v1.1 validation QA ingestion with crowd-authored questions, gold answer spans, and matched clean passages.
- [x] Add retrieval context Recall@k, gold-answer evidence coverage, and explicitly simulator-only extractive EM/F1 on SQuAD QA.
- [x] Run the full regression suite after SQuAD additions (39 passed).
- [x] Reprepare the public data with SQuAD and regenerate the full report/tables.
- [x] Regenerate the 78-second overview video with the SQuAD QA result and finish verification.

Use `make data` and `make all`; download failures are fatal rather than triggering synthetic fallback.

Real-model ASR remains unrun: no model, credentials, or explicit authorization were provided. The simulator output is labeled diagnostic-only, not ASR.

Final full suite: 39 tests passed. Full-size benchmark: 3,860 unique scanner groups (2 duplicate rows collapsed), 803 random-split held-out groups. BM25 was selected by the predeclared BIPIA-dev Recall@5 rule: 38.0% dev versus 15.7% hybrid and 4.6% word TF-IDF. On sealed test, BM25 achieved 43.2% BIPIA Recall@5 (95% CI 34.4–51.2) and 98.1% clean Wikipedia title-query Recall@5; hybrid scored 20.0% and 90.6%, respectively. Source-heldout D2 recall was 46.0% (95% CI 42.0–50.0) on BIPIA and 93.5% (91.2–95.2) on Tensor Trust; held-out benign-source FPRs are in the report/CSV. No real-model result is claimed.

The project default retrieval mode is now BM25, matching the development-selected candidate. Hybrid uses word TF-IDF dense ranking fused with BM25 by reciprocal rank fusion (RRF constant 60). The SQuAD v1.1 validation sample contains 1,200 crowd-authored questions over 941 unique gold passages; BM25 retrieves the paired passage in top 5 for 90.3% (95% CI 88.2–92.1) and gold-answer text appears in top-5 context for 88.9% (86.9–90.7). Simulator EM/F1 remain non-model diagnostics (EM 0.17%, token-F1 0.116). Final suite: 39 passed. Ruff is not installed in the current environment, so lint status was not reverified. The report, all tables/figures, and 78-second video are regenerated.
