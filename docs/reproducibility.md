# Reproducibility & Replication Guide

**Manuscript Title:** *How FP16 Vector Representation and TOAST Storage Layouts Shift Query Plan Selection in PostgreSQL: An Empirical and Cost-Model Study* (Manuscript V1.3.2)  
**Author:** Yash Pradhan  
**Target Venue:** IEEE Transactions on Knowledge and Data Engineering (TKDE) / IEEE ICDE  
**Repository Branch:** `research/planner-sensitivity`  
**Baseline Commit:** `11780d6ac733f0884d82a277823185f2c058b3af`  

---

## 1. Verified Experimental Environment

All published experimental measurements, plan captures, and execution latencies were generated in a strictly controlled local host environment:
- **Host OS:** Windows 11 Enterprise / Pro (`10.0.26200`, `x86_64`).
- **CPU:** Intel Core Ultra 9 185H (16 physical cores [6P + 8E + 2LPE], 22 logical threads).
- **RAM:** 32 GB LPDDR5 (31.43 GiB detected, 15.08 GiB available at baseline snapshot).
- **Storage:** Local NVMe SSD (Samsung / Western Digital).
- **Database Engine:** PostgreSQL 18.4 (`x86_64-windows`, compiled by MSVC 19.44.35227, 64-bit).
- **Extension:** `pgvector` 0.8.4 (with native `halfvec` support).
- **Python Runtime:** Python 3.13.14 with `psycopg` 3.3.4, `pgvector` 0.5.0, `matplotlib` 3.11.2, `pytest` 9.1.1.

### PostgreSQL 18.4 Server Parameters (Snapshot State)
- `shared_buffers = 128MB` (16,384 8 KiB pages)
- `effective_cache_size = 4GB` (524,288 8 KiB pages)
- `work_mem = 4MB` (4,096 KiB)
- `maintenance_work_mem = 64MB` (dynamically set to `1GB` during HNSW index builds)
- `effective_io_concurrency = 16`
- `io_combine_limit = 128kB` (16 pages)
- `max_parallel_workers_per_gather = 2` (disabled to `0` during transaction-scoped benchmarks)
- `random_page_cost = 4.0`, `seq_page_cost = 1.0`, `cpu_operator_cost = 0.0025` (Profile P4 baseline)

---

## 2. Three-Level Reproducibility Framework

This repository supports three distinct levels of scientific reproduction depending on external infrastructure availability:

```
┌────────────────────────────────────────────────────────────────────────┐
│ Level 1: Offline Statistical & Figure Reproduction (Zero DB required)  │
│  - Python standard library + matplotlib only.                          │
│  - Runs from verified CSV/JSONL artifacts in results/.                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Level 2: Database Experiment Execution (Local PostgreSQL + pgvector)   │
│  - Re-executes 972 plan captures, 18-scale sweep, exact validation.    │
│  - Uses pre-provisioned tables in compression_aware_rag_exp/scale.    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Level 3: Upstream Raw Dataset & Embedding Reconstruction (External)    │
│  - Requires raw BeIR/msmarco download and Ollama nomic-embed-text daemon.│
│  - Re-chunks text and regenerates 10,001 768-D vectors.                │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Level 1: Offline Analysis & Figure Reproduction (No Database Required)

Level 1 reproduces all statistical tests, tables, and figures directly from the published CSV/JSONL evidence without contacting a database.

### 3.1 Installation
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3.2 Run Offline Test Suite
Executes all 77 core precision-aware query planner and statistical unit tests:
```bash
pytest
```
*Expected output:* `77 passed in ~4.4s` (100% offline, zero network or database dependencies).

### 3.3 Reproduce Publication Figures (Figs 1, 2, 3)
Reads empirical CSVs and outputs 300-DPI PNGs into `paper/figures/generated/`:
```bash
python scripts/generate_paper_figures.py
```
*Outputs:*
- `paper/figures/generated/fig1_storage_and_cost_pipeline.png`
- `paper/figures/generated/fig2_scale_sweep_and_latency.png`
- `paper/figures/generated/fig3_retrieval_recall_and_ties.png`

### 3.4 Reproduce Statistical Tests (Friedman Omnibus & Wilcoxon Post-Hoc)
Computes tie-corrected Friedman omnibus tests ($df=8$), paired Wilcoxon signed-rank tests with Holm step-down adjustment, and bootstrap confidence intervals:
```bash
python scripts/analysis/analyze_phase3_sensitivity.py
```

### 3.5 Verify 486-Cell Candidate-Cost Validation Matrix (Offline Mode)
Verifies that closed-form Seq Scan + Top-k Sort costs match PostgreSQL optimizer outputs across all 486 cells:
```bash
python scripts/run_phase4f1_exact_validation.py --verify-only
```
*Expected output:* `Total cells validated: 486 | Exact cost matches (diff <= 0.01): 486 / 486 | Max cost diff: 0.0000`.

---

## 4. Level 2: Database Experiment Execution (PostgreSQL 18.4 + pgvector 0.8.4)

Level 2 executes live read-only query planning, candidate-cost validation, and latency benchmarks against local PostgreSQL databases.

> **Important Level 2 Scope Note**: Live execution requires pre-populated PostgreSQL scale databases (`compression_aware_rag_scale_500` through `compression_aware_rag_scale_5000`). The repository provides the 20 canonical query vectors in `recovered_query_vectors.csv` for plan capture, but does **not** bundle the 10,001 document corpus embeddings (~30 MB) due to upstream data licensing restrictions. Level 2 can be run only when the local database has already been populated with the experimental scale tables, or when full corpus embeddings have been acquired via Level 3. For immediate offline reproduction without a live database, use Level 1.

### 4.1 Database Preparation
Ensure PostgreSQL 18.4 and `pgvector` 0.8.4 are running on port `5432`. Configure `.env`:
```bash
copy .env.example .env
# Edit .env with your local PostgreSQL password
```

### 4.2 Pre-Flight Table Readiness Verification
Verify that all experimental tables, storage layouts (`EXTENDED` vs `PLAIN`), dimensions, and HNSW indexes are valid:
```bash
# Verify canonical baseline scale (N = 1,001) in compression_aware_rag_exp
python scripts/verify_table_readiness.py --scale 1001

# Verify scale tables (N = 5,000 and N = 10,000) in compression_aware_rag_scale
python scripts/verify_table_readiness.py --scale 5000
python scripts/verify_table_readiness.py --scale 10000
```

### 4.3 Live 486-Cell Candidate-Cost Validation
Executes 486 live read-only `EXPLAIN (SETTINGS, FORMAT JSON)` captures across 18 scales, 3 representations, and 9 planner profiles for canonical query $q_0$:
```bash
python scripts/run_phase4f1_exact_validation.py
```

### 4.4 Finalize 18-Scale Plan Sweep
Validates 972 captured execution plans, verifies table OID invariance, and outputs summary CSV:
```bash
python scripts/run_phase4e3_scale_sweep.py --finalize-existing
```

---

## 5. Level 3: Upstream Dataset Reconstruction & Scope Boundaries

### 5.1 Pre-bundled Inputs (Available in Repository)
- Canonical 10,001-chunk metadata: [`data/raw/msmarco_10k_canonical.meta.json`](../data/raw/msmarco_10k_canonical.meta.json) (`sha256 = cdca54aa145a8343916447f9b9fcd8ddcfdb72a3129c5263f5fba3c485434e8b` normalized Unix LF / `45c681d1573b83f469e8b71c7f74d587e48285f58561d2eb4c865293db650cd2` Windows CRLF).
- Canonical evaluation queries $q_0$–$q_{19}$ text: [`src/representations.py`](../src/representations.py) (lines 13–34).
- Canonical $q_0$ precomputed 768-D vector: [`results/planner_sensitivity/phase3_tie_sensitivity_20261031/recovered_query_vectors.csv`](../results/planner_sensitivity/phase3_tie_sensitivity_20261031/recovered_query_vectors.csv) (`sha256 = 4a0428709013d77d8d284b369cb144734421bfdc4f6e4a83faf17db8114cf478`).
- Precomputed reference top-10 chunk IDs: [`results/planner_sensitivity/phase3a_evidence_addendum_20261031/fp32_reference_top10_ids.csv`](../results/planner_sensitivity/phase3a_evidence_addendum_20261031/fp32_reference_top10_ids.csv).

### 5.2 Unbundled Upstream Inputs (Methodological Limitations)
As formally documented in Manuscript V1.3.2, Section VI-B Limitation (7):
1. **BeIR Document Selector:** The specific upstream document selector script that filtered 5,457 source documents from the BeIR MS-MARCO collection is not bundled in this repository.
2. **Batch Embedding Generator:** Recomputing embeddings from scratch requires installing optional dependencies (`pip install -r requirements-optional.txt`) and running an external Ollama daemon serving `nomic-embed-text:latest` on `http://127.0.0.1:11434`.
3. **Data Licensing:** The raw MS-MARCO text corpus is subject to the Microsoft Open Data License (research use only) and is preserved locally in `data/raw/msmarco_10k_canonical.tsv` (1.76 MB).

---

## 6. Cryptographic Artifact Hash Register

| Artifact Path | Size (Bytes) | SHA-256 Checksum |
| :--- | :---: | :--- |
| `phase4i_ieee_final_draft_v1.3.2.zip` | 6,016,862 | `b1cf115058dcd37697856e5dcc7e635e9f9dae1c458ad72fae4ee581b9733dbe` |
| `paper/final_research_paper_source_v1.3.2.md` | 130,763 | `fbc7ffbca63a5665a39626e25555d496a7dd7a0ffc5b9678e2e92c463f848f32` |
| `paper/final_claim_evidence_traceability_v1.3.2.csv` | 17,410 | `f28a39ec5c8bfef9ae61e685f0e34c26a575f0f37c3f918e77ce0a4427431e51` |
| `docs/source_level_cost_model_reconciliation.md` | 13,940 | `585d95d1d6a5e1cf3ba928a6fcf4a30e7efd37803d526fa17c768995a94ee881` |
| `results/planner_sensitivity/storage_results.csv` | 2,144 | `ed2d086360abc7aa58d8bf9452da5469c45b67da35e3b10abfff1b8e3ebce625` |
| `results/planner_sensitivity/scale_sweep_plan_only/scale_sweep_summary.csv` | 91,560 | `d91e80c7cd0ec617bbac1f3816c8a947bd2e6f787a785ab59a3c11dcaf6d4368` |
| `results/planner_sensitivity/scale_sweep_plan_only/scale_sweep_plans.jsonl` | 9,788,056 | `6887af68eaf0c594c4ee0ce8cfa0be50172b41eb37e97444368d99cf6cabcb7f` |
| `results/planner_sensitivity/scale_sweep_plan_only/scale_sweep_storage.csv` | 12,019 | `58ad9538c7a9df0afc8e9491aedb7cb8becb1984ded5cea6d84d7b094c20dca9` |
| `results/planner_sensitivity/phase4f1_validation/seq_cost_formula_validation.csv` | 39,841 | `ae7b243ec903cbef858a74e92ebdb55fa3dc9bc546f5e3be5b026649f4305885` |
| `results/planner_sensitivity/phase3_tie_sensitivity_20261031/recovered_query_vectors.csv` | 186,527 | `e559591e13a9d90ecb5f12e1a3bcdaee3a479a32cba726359d99d14691c9b68e` |
| `results/planner_sensitivity/full_run_20261031_01/diagnostic_root_buffer_summary.csv` | 2,529 | `b8c9916909ffc648a3e61d17e34f1553484f4fd79582d9e5e21e7d7e8d5bbe5e` |
| `scripts/run_phase4e3_scale_sweep.py` | 66,410 | `13b693f33b5257a13ff0db62e63f054e6fac7e9997f1ad2f608366c3574b8f32` |
