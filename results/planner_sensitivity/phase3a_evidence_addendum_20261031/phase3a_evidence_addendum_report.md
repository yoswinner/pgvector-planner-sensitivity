# Phase 3A.1 Evidence Chain Closure Addendum Report

**Project:** Precision-Aware Query Planning for Vector Retrieval in PostgreSQL  
**Repository:** `yoswinner/CompressionAwareRag`  
**Git Commit SHA:** `8dfdce0a00338d0c6e0c4f70ea3e83d40e9b93ee`  
**Audit Directory:** `C:\Coding\GenAI\Projects\CompressionAwareRag\results\planner_sensitivity\phase3a_evidence_addendum_20261031`  
**Timestamp:** `2026-10-30T21:04:54.341417+00:00`

---

## 1. Executive Summary

This independent addendum audit closes the three provenance and reproducibility gaps identified during review:
1. **Explicit Ground-Truth Reference IDs:** Retrieved and exported the complete set of 600 FP32 reference top-10 document IDs and exact cosine distances (`fp32_reference_top10_ids.csv`).
2. **Independent Recall Recalculation:** Independently recalculated conventional Recall@10 from document-ID set intersections across all 1,980 query-condition units. **100.0% of units (1,980 / 1,980)** matched both Phase 3A and Phase 2 values with zero mismatches.
3. **Forced-HNSW GUC Equivalence:** Audited the `enable_bitmapscan` setting discrepancy (Phase 2 `on` vs Phase 3A `off`) across all 180 forced-HNSW units. **100.0% of units (180 / 180)** demonstrated strict physical and candidate equivalence.
4. **Script Provenance:** Confirmed that `scripts/run_phase3a_tie_sensitivity.py` and the archived entry in `Phase3A_Tie_Sensitivity_Evidence_20261031.zip` are **100% byte-identical** (`57d37e06097fe79e7bf0ff60f375c349a407dd0efd333c846127455e7240a97e`).

---

## 2. FP32 Reference Top-10 Document IDs & Ordering Policy

- **File:** `fp32_reference_top10_ids.csv` (600 rows: 3 scales $\times$ 20 queries $\times$ 10 ranks)
- **Execution:** Strictly sequential scan (`enable_indexscan=off, enable_bitmapscan=off, enable_seqscan=on, max_parallel_workers_per_gather=0`) on `chunks_<scale>_fp32_extended`.
- **Query Ordering Policy:**
  ```sql
  SELECT chunk_id, (embedding <=> %s::vector(768)) AS distance
  FROM planner_sensitivity.chunks_<scale>_fp32_extended
  ORDER BY distance ASC
  LIMIT 10;
  ```
- **Tie-Breaking Determinism:**
  The query intentionally uses `ORDER BY distance ASC` without a secondary tie-breaker column (e.g. `chunk_id ASC`). Because PostgreSQL's sequential scan traverses the physical table blocks sequentially and top-N heapsort retains the first-encountered equal elements, the selection of boundary-tied documents is deterministic across repeated executions in the absence of table mutations.

---

## 3. Independent Conventional Recall@10 Reconciliation

- **File:** `conventional_recall_independent_reconciliation.csv` (1,980 rows)
- **Methodology:**
  For each of the 1,980 query-condition units, the candidate top-10 IDs from `tie_sensitivity_query_results.csv` were intersected with the newly exported FP32 reference top-10 IDs:
  $$\text{Recall@10} = \frac{|S \cap \text{Top-10}_{\text{ref}}|}{10}$$
- **Reconciliation Audit Results:**
  - Total Units Evaluated: **1,980**
  - Matches with Phase 3A exported conventional recall: **1,980 / 1,980 (100.0%)**
  - Matches with Phase 2 original conventional recall: **1,980 / 1,980 (100.0%)**
  - Discrepancies / Mismatches: **0**

---

## 4. Forced-HNSW `enable_bitmapscan` Setting Discrepancy & Equivalence Audit

- **Discrepancy Identification:**
  - **Phase 2 Runner (`src/planner_sensitivity_experiment.py`):** Configured forced-HNSW with `enable_indexscan = on`, `enable_seqscan = off`, and `enable_bitmapscan = on`.
  - **Phase 3A Script (`scripts/run_phase3a_tie_sensitivity.py`):** Configured forced-HNSW with `enable_indexscan = on`, `enable_seqscan = off`, and `enable_bitmapscan = off`.
- **Engine-Level Analysis:**
  In PostgreSQL 18 with `pgvector`, HNSW indexes only support `Index Scan` operator access paths for `ORDER BY ... LIMIT` queries. HNSW operator classes do not support `Bitmap Index Scan`. Therefore, `enable_bitmapscan` has no effect on forced-HNSW query planning.
- **Empirical Paired Equivalence Test (`phase3a_guc_equivalence_audit.csv`):**
  Evaluated all 180 forced-HNSW units under both `enable_bitmapscan = on` and `enable_bitmapscan = off`:
  - Plan scan node matched: **180 / 180 (100.0% Index Scan)**
  - Plan index name matched: **180 / 180 (100.0%)**
  - Retrieved candidate top-10 IDs matched: **180 / 180 (100.0% bitwise identical)**
  - Discrepancies: **0**

---

## 5. Script Provenance Audit

- **File:** `script_provenance_audit.json`
- **Disk Script:** `scripts/run_phase3a_tie_sensitivity.py` (36,107 bytes, SHA-256: `57d37e06097fe79e7bf0ff60f375c349a407dd0efd333c846127455e7240a97e`)
- **Archived Entry:** `Phase3A_Tie_Sensitivity_Evidence_20261031/run_phase3a_tie_sensitivity.py` in `Phase3A_Tie_Sensitivity_Evidence_20261031.zip` (36,107 bytes, SHA-256: `57d37e06097fe79e7bf0ff60f375c349a407dd0efd333c846127455e7240a97e`)
- **Conclusion:** Both files are **100% byte-identical**.

---

## 6. Artifact Integrity

All original Phase 2, Phase 2A, and Phase 3A files remain completely unchanged.
