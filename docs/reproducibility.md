# Reproducibility & Replication Guide

**Manuscript Title:** *How FP16 Vector Representation and TOAST Storage Layouts Shift Query Plan Selection in PostgreSQL: An Empirical and Cost-Model Study* (Manuscript V1.3.3 Accepted Baseline; Historical V1.3.2 Preserved)  
**Author:** Yash Pradhan  
**Manuscript Format:** IEEE Computer Society Two-Column Format (Venue Unselected)  
**Repository Branch:** `research/planner-sensitivity`  
**Baseline Commit:** `11780d6ac733f0884d82a277823185f2c058b3af`  

> **Bounded Reproduction Scope**: The proposed Git clone is structurally self-consistent and passes the documented offline verification checks. Full from-scratch experimental reproduction remains subject to the limitations documented in this reproducibility section. Preserved evidence supports offline reproduction of post-collection cost-model calculations, statistics, bootstrap confidence intervals, tables and figures, without establishing full from-scratch reproduction of upstream corpus acquisition, embeddings or physical database/index state.

---

## 1. Verified Experimental Environment

All published experimental measurements, plan captures, and execution latencies were collected on the recorded host using the documented software versions and configuration snapshots. This documentation records the observed host configuration and captured parameters, without implying that all external system conditions, background operating system processes, or host-level resource contention were controlled or independently verified. The specifications below distinguish between the recorded host hardware and software environment, captured PostgreSQL server configuration snapshots, and parameters dynamically altered for specific benchmark operations or transactions.

### 1.1 Recorded Host and Software Environment
- **Host OS:** Windows 11 Enterprise / Pro (`10.0.26200`, `x86_64`).
- **CPU:** Intel Core Ultra 9 185H (16 physical cores [6P + 8E + 2LPE], 22 logical threads).
- **RAM:** 32 GB LPDDR5 (31.43 GiB detected, 15.08 GiB available at baseline snapshot).
- **Storage:** Local PCIe 4.0 NVMe SSD (SK Hynix 1TB, `SKHynix_HFS001TEJ4X112N`).
- **Database Engine:** PostgreSQL 18.4 (`x86_64-windows`, compiled by MSVC 19.44.35227, 64-bit).
- **Extension:** `pgvector` 0.8.4 (with native `halfvec` support).
- **Python Runtime:** Python 3.13.14 with `psycopg` 3.3.4, `pgvector` 0.5.0, `matplotlib` 3.11.2, `pytest` 9.1.1.

### 1.2 Captured PostgreSQL Configuration (Server Baseline Snapshot)
The following server parameters reflect the baseline configuration snapshot captured in `results/planner_sensitivity/full_run_20261031_01/environment_snapshot.json`:
- `shared_buffers = 128MB` (16,384 8 KiB pages)
- `effective_cache_size = 4GB` (524,288 8 KiB pages)
- `work_mem = 4MB` (4,096 KiB)
- `maintenance_work_mem = 64MB` (server baseline)
- `effective_io_concurrency = 16`
- `io_combine_limit = 128kB` (16 pages)
- Server default cost parameters: `random_page_cost = 4.0`, `seq_page_cost = 1.0`, `cpu_tuple_cost = 0.01`, `cpu_index_tuple_cost = 0.005`, `cpu_operator_cost = 0.0025` (Profile P4 baseline).

### 1.3 Parameters Dynamically Changed During Benchmark Operations
Certain PostgreSQL parameters were not held constant across every experimental operation, but were dynamically altered at session or transaction scope:
- **Parallel Workers:** `max_parallel_workers_per_gather` (server default `2`) was dynamically set to `0` for the relevant benchmark executions to exclude parallel-worker plans from the tested configuration and isolate single-worker cost models. (This parameter change excludes parallel-worker plans; it does not claim or guarantee deterministic plan selection or execution).
- **Maintenance Memory:** `maintenance_work_mem` was dynamically increased from `64MB` to `1GB` during HNSW index builds to ensure sufficient memory for graph construction.
- **Cost-Model Profile Parameters:** Planner cost weights (`seq_page_cost`, `random_page_cost`, `cpu_tuple_cost`, `cpu_index_tuple_cost`, and `cpu_operator_cost`) were systematically varied across 9 distinct planner profiles (P1 through P9) via transaction-scoped `SET LOCAL` statements to evaluate optimizer sensitivity across storage configurations.
- **Scan Enforcement GUCs:** Planner scan switches (`enable_seqscan` and `enable_indexscan`) were dynamically toggled between `on` and `off` to force alternative scan candidates (`force_seq`, `force_idx`) and extract ground-truth candidate costs for boundary-tie verification.

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
│  - Evaluates live query plans, 18-scale sweep, exact cost validation.  │
│  - Connects to pre-provisioned catalogs (compression_aware_rag_exp/    │
│    compression_aware_rag_scale); read-only execution.                  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ Level 3: Proposed Upstream Dataset & Embedding Reconstruction (Ext.)   │
│  - Hypothetical from-scratch pipeline via BeIR/msmarco and Ollama.     │
│  - Subject to upstream shard order, unbundled selector, & model tag    │
│    mutability limits; not required for Level 1 reproduction.           │
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
The verified and reproducible offline test procedure explicitly executes the two core research test modules:
```bash
python -m pytest tests/test_planner_sensitivity_experiment.py tests/test_analysis_pipeline.py -v
```
*(Alternatively, executing `pytest` from the repository root targets the same two modules via `testpaths` defined in `pytest.ini`.)*

- **Expected result:** 77 tests passed. Observed execution times ranged from approximately 0.3 to 4.4 seconds across tested environments and execution conditions (100% offline, zero network or database dependencies).
- **Test Suite Breakdown:** Exactly 77 tests across the two specified modules:
  - 64 planner sensitivity and cost-model unit tests in [`tests/test_planner_sensitivity_experiment.py`](../tests/test_planner_sensitivity_experiment.py).
  - 13 statistical inference and reconciliation tests in [`tests/test_analysis_pipeline.py`](../tests/test_analysis_pipeline.py).
- **Verification Boundary:** Verification is strictly bounded to these 77 offline unit and statistical tests. This verification confirms analytical cost models, planner logic, and statistical pipelines, but does not claim that every repository test, integration test, or end-to-end database workflow has been verified.

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

### 3.5 Verify 486-Cell Candidate-Cost Validation Matrix (Supplementary Validation, Offline Mode)
Verifies that closed-form Seq Scan + Top-k Sort costs match PostgreSQL optimizer outputs across all 486 cells (18 scales $\times$ 3 representations $\times$ 9 planner profiles for canonical query $q_0$):
```bash
python scripts/run_phase4f1_exact_validation.py --verify-only
```
*Expected output:* `Total cells validated: 486 | Exact cost matches (diff <= 0.01): 486 / 486 | Max cost diff: 0.0000`.

---

## 4. Level 2: Database Experiment Execution (PostgreSQL 18.4 + pgvector 0.8.4)

Level 2 executes live read-only query planning, candidate-cost validation, and latency benchmarks against local PostgreSQL databases.

> **Important Level 2 Scope Note**: Live execution requires pre-populated PostgreSQL databases: `compression_aware_rag_exp` (canonical baseline tables at $N=1,001$) and `compression_aware_rag_scale` (multi-scale sweep tables across $N \in [500, 10000]$). The repository provides the 20 canonical query vectors in `recovered_query_vectors.csv` for plan capture, but does **not** bundle the complete document corpus embeddings (10,000 database target rows from 10,001 deterministic chunks across 5,457 source documents, ~30 MB) due to upstream data licensing boundaries. Level 2 can be run only when the local database has already been populated with the experimental scale tables, or when full corpus embeddings have been acquired via Level 3. For immediate offline reproduction without a live database, use Level 1.

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

### 4.3 Live 486-Cell Candidate-Cost Validation (Supplementary Analytical Validation)
Executes 486 live read-only `EXPLAIN (SETTINGS, FORMAT JSON)` captures across 18 scales, 3 representations, and 9 planner profiles for canonical query $q_0$ to validate the analytical sequential scan cost model:
```bash
python scripts/run_phase4f1_exact_validation.py
```

### 4.4 Finalize 18-Scale Plan Sweep (Supplementary Scale-Sweep Experiment)
Validates 972 captured execution plans (18 scales $\times$ 3 representations $\times$ 9 profiles $\times$ 2 scan modes for query $q_0$), verifies table OID invariance, and outputs summary CSV:
```bash
python scripts/run_phase4e3_scale_sweep.py --finalize-existing
```

---

## 5. Level 3: Upstream Dataset Reconstruction & Scope Boundaries

### 5.1 Pre-bundled Inputs (Available in Repository)
- Canonical text corpus metadata: [`data/raw/msmarco_10k_canonical.meta.json`](../data/raw/msmarco_10k_canonical.meta.json) (5,457 source documents, 10,001 deterministic text chunks, 10,000 database target rows; Unix LF sha256: `cdca54aa145a8343916447f9b9fcd8ddcfdb72a3129c5263f5fba3c485434e8b` / Windows CRLF sha256: `45c681d1573b83f469e8b71c7f74d587e48285f58561d2eb4c865293db650cd2`).
- Canonical evaluation queries $q_0$–$q_{19}$ text: [`src/representations.py`](../src/representations.py) (lines 13–34).
- Canonical $q_0$ precomputed 768-D vector: [`results/planner_sensitivity/phase3_tie_sensitivity_20261031/recovered_query_vectors.csv`](../results/planner_sensitivity/phase3_tie_sensitivity_20261031/recovered_query_vectors.csv).
- Precomputed reference top-10 chunk IDs: [`results/planner_sensitivity/phase3a_evidence_addendum_20261031/fp32_reference_top10_ids.csv`](../results/planner_sensitivity/phase3a_evidence_addendum_20261031/fp32_reference_top10_ids.csv).

### 5.2 Unbundled Upstream Inputs (Methodological Limitations)
As formally documented in Manuscript V1.3.3, Section VI-B Limitation (7):
1. **BeIR Document Selector:** The specific upstream document selector script that filtered 5,457 source documents from the BeIR MS-MARCO collection is not bundled in this repository.
2. **Batch Embedding Generator:** Recomputing embeddings from scratch requires installing optional dependencies (`pip install -r requirements-optional.txt`) and running an external Ollama daemon serving `nomic-embed-text:latest` on `http://127.0.0.1:11434`.
3. **Data Licensing and Redistribution Boundaries:** The research involves distinct intellectual property and licensing considerations:
   - *Upstream Dataset Terms:* The MS MARCO dataset was released under the **[Microsoft MS MARCO Terms of Use (Non-Commercial Research Use Agreement)](https://microsoft.github.io/msmarco/)**, intended for non-commercial research use, with no licence or other intellectual-property rights granted over the underlying dataset or third-party web content.
   - *BeIR Repository Licence Declaration:* The Hugging Face repository for [`BeIR/msmarco`](https://huggingface.co/datasets/BeIR/msmarco) declares `cc-by-sa-4.0` in its repository licence metadata. This repository declaration does not independently establish rights to redistribute underlying MS MARCO passages or third-party web content.
   - *Third-Party Web Content Rights:* Passages extracted from web pages and search results remain subject to the copyrights and intellectual property rights of the respective original content authors and web publishers.
   - *Project Code and Documentation Licence:* The repository's **[Apache 2.0 License](../LICENSE)** applies strictly to original research software, experiment harnesses, analysis scripts, and documentation—it does not grant licences over third-party corpus content.
   - *Redistribution Policy:* To adhere strictly to copyright boundaries and upstream terms, the raw TSV file (`msmarco_10k_canonical.tsv`, 1.76 MB) is intentionally not bundled in this public replication repository (it is preserved in the local research archive and original development repository). Downstream users should acquire the corpus directly from upstream sources ([`BeIR/msmarco`](https://huggingface.co/datasets/BeIR/msmarco)) as documented in [`docs/DATA_ACQUISITION.md`](DATA_ACQUISITION.md).

---

## 6. Cryptographic Artifact Hash Register

The following register records verified cryptographic SHA-256 hashes and byte lengths for all 22 primary publication assets, evidence files, and execution harnesses present in a fresh Git clone of this repository (synchronized with [`MANIFEST.json`](../MANIFEST.json)):

| Artifact Path | Size (Bytes) | SHA-256 Checksum |
| :--- | :---: | :--- |
| `paper/final_research_paper_v1.3.3.pdf` | 2,357,409 | `d2a5fe8589d1c66e01e74ddb87bfcd538d4cf7c3e430973e05864e2857487c9c` |
| `paper/final_research_paper_v1.3.3.docx` | 3,591,305 | `e208f4c6c0949af90425878aaff9232617568396dc54c8677b27241b6e0a237b` |
| `paper/final_research_paper_source_v1.3.3.md` | 131,397 | `fe5b75e85b5e093e5189af68b4498699921dd81fce29bac46873a6f84b4d4862` |
| `paper/phase5c_content_preservation_and_formatting_qa_report_v1.3.3.md` | 17,160 | `17bb09c60a91facdf3220542f9759f37544de5cb173f718cfff0cf1cff8fd64b` |
| `paper/build_ieee_a4_manuscript_v2.py` | 76,218 | `a347baf4cc71f13ac481cb23ac0df89e43f3b5eb512067c969a0ea0b6637a4e8` |
| `paper/verify_ieee_a4_manuscript_v2.py` | 47,136 | `02a76bd5ffdd2bdef7b7f5cf4aa5d8505442ae2100773ca3ebeb586704467555` |
| `paper/final_research_paper_source_v1.3.2.md` | 130,763 | `8d3b670a9320fe429c9e4fab4f1981afe4a505404a7e437101ffce95f9d5ab4f` |
| `paper/final_claim_evidence_traceability_v1.3.2.csv` | 17,410 | `e71e8c8b7eaaa7d99ca58590cfd345fe4c2403db02e1656d01e46e3cfa0b47de` |
| `paper/final_reference_audit_v1.3.2.csv` | 22,592 | `6b3a7106e39cbde35e81e96d87c0877a56e399d746b1e13d03cdd42ff68035ea` |
| `docs/source_level_cost_model_reconciliation.md` | 13,927 | `234d1a209dd9528450be567f94fad5bb08493f9d7bca0dcc78b587039e3194ad` |
| `docs/DATA_ACQUISITION.md` | 13,393 | `0cbec742b46643a751c6c90bd588a256ff4243bc4eb05c3ea7df59410fcc87ef` |
| `results/planner_sensitivity/storage_results.csv` | 2,144 | `ed2d086360abc7aa58d8bf9452da5469c45b67da35e3b10abfff1b8e3ebce625` |
| `results/planner_sensitivity/full_run_20261031_01/summary_results.csv` | 90,334 | `2640a084fbb8e906efd1d929f2a4570d0bd568476f96f718ebcbdb3723810b0e` |
| `results/planner_sensitivity/full_run_20261031_01/diagnostic_root_buffer_summary.csv` | 2,529 | `b8c9916909ffc648a3e61d17e34f1553484f4fd79582d9e5e21e7d7e8d5bbe5e` |
| `results/planner_sensitivity/scale_sweep_plan_only/scale_sweep_summary.csv` | 91,560 | `d91e80c7cd0ec617bbac1f3816c8a947bd2e6f787a785ab59a3c11dcaf6d4368` |
| `results/planner_sensitivity/scale_sweep_plan_only/scale_sweep_storage.csv` | 12,019 | `58ad9538c7a9df0afc8e9491aedb7cb8becb1984ded5cea6d84d7b094c20dca9` |
| `results/planner_sensitivity/phase4f1_validation/seq_cost_formula_validation.csv` | 39,841 | `7cff773f400e66ae118311206e4cf67fadba2dbf388de96602c926e922d46f40` |
| `results/planner_sensitivity/phase3_tie_sensitivity_20261031/recovered_query_vectors.csv` | 186,527 | `c58dcef0c9e2ab26dd8000bef8d1dc64b8f7980e02cd6827b866daabf9f50ef8` |
| `scripts/run_phase4e3_scale_sweep.py` | 66,410 | `13b693f33b5257a13ff0db62e63f054e6fac7e9997f1ad2f608366c3574b8f32` |
| `scripts/run_phase4f1_exact_validation.py` | 12,922 | `8f2a8498151ac628bed7e7ceb27273e7d8020b19edce6f2e1971b7b4dd36bde0` |
| `scripts/generate_paper_figures.py` | 17,685 | `7ba6ac52474cab9279d92fa0cd260d697d4b74cec56df8e114c66a10bfcceb9a` |
| `scripts/analysis/analyze_phase3_sensitivity.py` | 26,374 | `3cdf202b0c8cbcc133502e6bc3b3ad626dc1dcc9cb209e1737a08740b52ac6ac` |

> [!NOTE]
> **Archival Distribution Packages (Not Tracked in Git Clone):**
> - **V1.3.3 Manuscript Distribution Package:** The complete V1.3.3 manuscript package was distributed as `ieee_a4_review_v2_2_v1.3.3.zip` (10,263,098 bytes; SHA-256 `4a0c615000510f3d1227c132afa9e5ba9780d424ab1b519ca29ea752e3bf2d72`). In this repository, its constituent publication assets, figures, and verification harnesses are tracked individually under `paper/` rather than as a monolithic archive, and `*.zip` files are excluded by `.gitignore`.
> - **Historical V1.3.2 Review Package:** The legacy review draft archive (`submission/ieee_a4_review_v1.zip`, 3,592,217 bytes; SHA-256 `299b029aae9f404c2275374bc703cbbcf083bfb631b3f64234bd3684dff73858`) is retained as an archival artifact.
> - **Archival Preservation:** Both ZIP packages are permanently preserved in the local research archive (`C:\Research\PrecisionAwareVectorRetrieval_Archive\`) and the original research repository (`CompressionAwareRag`). Neither ZIP is expected to exist in a fresh Git clone; their hashes are recorded here strictly for archival provenance.
