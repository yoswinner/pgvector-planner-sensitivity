# Phase 4E.3 — Timing Provenance and Runtime Instrumentation Note

## 1. Overview and Scope

This document provides the authoritative reconciliation of timing provenance, instrumentation scope, and wall-clock execution semantics for the Phase 4E.3 18-scale plan-only query-planner parameter sweep on PostgreSQL 18.4 and pgvector 0.8.4.

It accompanies `scale_sweep_manifest.json`, `scale_sweep_analysis.md`, and the execution audit logs, clarifying the distinction between:
1. Individual recorded phase durations measured by component timers.
2. The arithmetic sum of recorded phase durations.
3. The overall multi-stage workflow elapsed timestamps.
4. The artifact-finalization execution timestamps.
5. Continuous end-to-end wall-clock duration semantics.

---

## 2. Component Phase Durations (Recorded Timers)

The experiment runner (`scripts/run_phase4e3_scale_sweep.py`) instrumented discrete operational phases using Python `time.perf_counter()` timers during execution:

| Operational Phase | Scope / Description | Recorded Duration |
| :--- | :--- | :--- |
| **Table Provisioning** | Deterministic prefix CTAS slicing from canonical 10,001-chunk dataset for 16 intermediate scales ($N \in [500, 4000]$, excluding pre-existing $N=1001$ and $N=5000$) across 3 representations (`fp32_extended`, `fp32_plain`, `fp16_extended`). Total: 48 tables. | `5.7500 s` |
| **HNSW Construction & ANALYZE** | Index creation (`m=16`, `ef_construction=64`, `vector_cosine_ops` / `halfvec_cosine_ops`) and PostgreSQL catalog statistics collection (`ANALYZE`) on all 48 newly provisioned tables. | `31.6700 s` |
| **EXPLAIN Capture** | Read-only execution of 972 `EXPLAIN (SETTINGS, FORMAT JSON)` statements (18 scales $\times$ 3 representations $\times$ 9 profiles $\times$ 2 modes for canonical query $q_0$). | `5.0570 s` |
| **Sum of Recorded Phases** | Arithmetic sum of the three discrete component timers: $5.7500 + 31.6700 + 5.0570$. | **`42.4770 s`** |

> [!IMPORTANT]
> The value `42.477 s` represents the **arithmetic sum of discrete phase timers**, not an independently verified continuous end-to-end wall-clock duration. It isolates the active compute and I/O time spent directly executing database DDL, indexing, and EXPLAIN queries.

---

## 3. Overall Multi-Stage Workflow Provenance

The complete experimental workflow spanned initial invocation, diagnostic evaluation of PostgreSQL optimizer fuzzy tie-breaking, catalog validation, and artifact finalization:

| Workflow Milestone | Timestamp (UTC) | Notes |
| :--- | :--- | :--- |
| **Initial Workflow Start** | `2026-10-31T16:25:08.139125+00:00` | Initiated via background task (`task-3393`) invoking `scripts/run_phase4e3_scale_sweep.py`. Provisioning, index building, and all 972 plan captures completed. |
| **Fuzzy Tie-Break Exception** | `2026-10-31T16:25:52+00:00` | The script halted on a post-capture validation assertion at $N=850, \text{fp32\_plain}, \text{P6}$ because it strictly required $\text{total\_cost}(\text{HNSW}) \le \text{total\_cost}(\text{SeqScan}) + 0.01$. The planner had selected `Index Scan` at total cost `846.04` vs. SeqScan `843.86` (+0.258%). |
| **Diagnostic & Algorithmic Audit** | `2026-10-31T16:26:00` – `16:35:20` | Confirmed PostgreSQL's `compare_path_costs_fuzzily` (`STD_FUZZ_FACTOR = 1.01` in `src/backend/optimizer/util/pathnode.c`) treats total costs within 1% as fuzzily tied and breaks ties on lower startup cost (`814.52 < 835.01`). The runner was updated with this optimizer rule and `--finalize-existing` support. |
| **Workflow Completion** | `2026-10-31T16:35:30.225581+00:00` | Validation suite completed across all 32 database objects, 972 plans, and 54 storage rows. |
| **Total Elapsed Workflow Span** | **`622.086 s`** (10 min 22.086 s) | Elapsed span between initial workflow invocation and final artifact release. |

---

## 4. Artifact Finalization Timestamps

When invoked with `--finalize-existing` to process the on-disk plan captures and catalog metrics without re-running DDL or captures:

- **Finalization Start:** `2026-10-31T16:35:28.139125+00:00`
- **Finalization Completed:** `2026-10-31T16:35:30.225581+00:00`
- **Finalization Elapsed:** `2.086456 s` ($\approx 2.086\text{ s}$)

During this 2.086-second finalization window:
- 54 storage rows were verified against live PostgreSQL catalog snapshots.
- 972 plan captures from `scale_sweep_plans.jsonl` were parsed and mapped.
- 486 summary records were generated, verifying the 1% fuzzy tiebreak at $N=850$.
- 486/486 analytical guard formulas were independently evaluated.
- All 32 catalog objects (11 in `compression_aware_rag_exp`, 21 in `compression_aware_rag_scale`) were confirmed identical to pre-run snapshots.
- `scale_sweep_summary.csv`, `scale_sweep_analysis.md`, and `scale_sweep_manifest.json` were produced.

---

## 5. End-to-End Wall-Clock Semantics and Reporting Policy

To maintain scientific integrity and precision in reporting:

1. **End-to-End Wall-Clock Duration:** Explicitly recorded as `null` / `unavailable`. A single uninterrupted continuous wall-clock benchmark figure cannot be claimed because execution encompassed discrete stages: initial provisioning/indexing/capture, diagnostic audit of optimizer cost comparison fuzziness, and finalization validation.
2. **Phase Timer Sum:** The figure `42.477 s` must always be identified as the sum of recorded phase component timers ($5.750\text{ s} + 31.670\text{ s} + 5.057\text{ s}$), reflecting raw database execution time.
3. **Log File Integrity:**
   - `logs/task-3393_initial_run.log` preserves the unmodified console output and traceback from the initial execution run.
   - `logs/execution_and_validation.log` preserves the complete workflow timeline and validation audit log spanning the full 622.086-second workflow.

