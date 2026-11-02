# Query Vector `q0` SHA-256 Hash Reconciliation Report

**Project:** Precision-Aware Query Planning for Vector Retrieval in PostgreSQL  
**Phase:** Phase 4E.3 — Post-Execution Artifact Audit  
**Date:** 2026-10-31  
**Author:** Yash Pradhan  

---

## 1. Executive Summary

During the Phase 4E.3 preflight report, a provisional hash prefix `f01297be...` was recorded in the execution plan text:
> *"Load `query_id = 0` (`q0`) directly from `results/planner_sensitivity/phase3_tie_sensitivity_20261031/recovered_query_vectors.csv` and verify its SHA-256 (`f01297be...`)."*

However, during execution and in the final experimental manifest ([`scale_sweep_manifest.json`](scale_sweep_manifest.json)), the recorded SHA-256 hash for `q0` is:
> **`4a0428709013d77d8d284b369cb144734421bfdc4f6e4a83faf17db8114cf478`**

This investigation reconciles this discrepancy:

1. **Different Vectors vs. Same Vector:** **There is only ONE query vector.** The underlying query vector `q0` (corresponding to evaluation query 0: `"what is routing in computer networks"`) is identical across Phase 3, Phase 3A, and Phase 4E.3. No embeddings were regenerated.
2. **Authoritative Hash Origin:** The hash `4a042870...` is the authoritative, verified SHA-256 hash recorded in [`recovered_query_vectors.csv`](file:///c:/Coding/GenAI/Projects/CompressionAwareRag/results/planner_sensitivity/phase3_tie_sensitivity_20261031/recovered_query_vectors.csv) when the vector was extracted during Phase 3A.
3. **Preflight Origin:** The string `f01297be...` was an unverified placeholder prefix introduced in the preflight narrative response before the vector file had been loaded into Python for live hash evaluation. It does not correspond to any vector, file, or serialization in the repository.

---

## 2. Technical Provenance of `q0`

### A. Source Extraction in Phase 3A
In Phase 3A, [`scripts/analysis/run_phase3a_tie_sensitivity.py`](file:///c:/Coding/GenAI/Projects/CompressionAwareRag/scripts/analysis/run_phase3a_tie_sensitivity.py) recovered evaluation query vectors from the raw plan captures in [`results/planner_sensitivity/full_run_20261031_01/plan_capture.jsonl`](file:///c:/Coding/GenAI/Projects/CompressionAwareRag/results/planner_sensitivity/full_run_20261031_01/plan_capture.jsonl):

```python
# From scripts/analysis/run_phase3a_tie_sensitivity.py (lines 170-171):
vec_serialized = json.dumps(vec_floats)
vec_hash = hashlib.sha256(vec_serialized.encode("utf-8")).hexdigest()
```

The 20 query vectors were written to [`recovered_query_vectors.csv`](file:///c:/Coding/GenAI/Projects/CompressionAwareRag/results/planner_sensitivity/phase3_tie_sensitivity_20261031/recovered_query_vectors.csv). Row 2 (the first data row) is:

```csv
query_id,dimension,sha256,serialized_vector
0,768,4a0428709013d77d8d284b369cb144734421bfdc4f6e4a83faf17db8114cf478,"[0.76213634, 1.2331034, -2.5730884, -0.11761875, 0.036621965, 1.2167987, -0.95584416, ...]"
```

### B. Live Verification in Phase 4E.3
In Phase 4E.3, [`scripts/run_phase4e3_scale_sweep.py`](file:///c:/Coding/GenAI/Projects/CompressionAwareRag/scripts/run_phase4e3_scale_sweep.py) enforced cryptographic verification before executing any `EXPLAIN` captures:

```python
EXPECTED_Q0_SHA256 = "4a0428709013d77d8d284b369cb144734421bfdc4f6e4a83faf17db8114cf478"
```

The function `load_and_verify_canonical_q0()`:
1. Loaded row `query_id = 0` from `recovered_query_vectors.csv`.
2. Computed `hashlib.sha256(vec_str.encode("utf-8")).hexdigest()`.
3. Asserted exact equality with both the recorded CSV column and `EXPECTED_Q0_SHA256`.
4. Parsed the 768 IEEE-754 float values directly from that verified string.

---

## 3. Cryptographic Hashes of `q0` Across Serializations

To establish exact reproducibility across any consumer tools, the table below documents the cryptographic hashes of `q0` under multiple standard representations:

| Representation / Encoding | Specification | SHA-256 Checksum |
| :--- | :--- | :--- |
| **Authoritative JSON String (UTF-8)** | `json.dumps(vec_floats)` as stored in `recovered_query_vectors.csv` | **`4a0428709013d77d8d284b369cb144734421bfdc4f6e4a83faf17db8114cf478`** |
| **IEEE-754 Float32 (Little-Endian Binary)** | 768 $\times$ 4 bytes = 3,072 bytes (`<768f`) | **`3f5a10a6816f561587d427c56c11ec08586b587690262df8a8060150341969dd`** |
| **IEEE-754 Float32 (Big-Endian Binary)** | 768 $\times$ 4 bytes = 3,072 bytes (`>768f`) | **`2f7189871d386032ba483219018cb00b71d77e5947975780355f379b1e77b498`** |
| **IEEE-754 Float64 (Little-Endian Binary)** | 768 $\times$ 8 bytes = 6,144 bytes (`<768d`) | **`6dd95da47b0c4bfc5e1892d8b2dd2d6cdbf93c1957ce7f84101480dd3e5dac02`** |
| **Query Text (UTF-8)** | `"what is routing in computer networks"` | **`8343991994646c9683db103219f01562a391f6f6adbda36fdad387581d760d4a`** |

---

## 4. Vector Values Head and Tail

The 768-dimensional float coordinates for `q0` match across all phases:

- **Dimensions:** 768
- **Coordinates [0..9]:**
  `[0.76213634, 1.2331034, -2.5730884, -0.11761875, 0.036621965, 1.2167987, -0.95584416, 0.27670082, -0.6154418, 0.61164045]`
- **Coordinates [758..767]:**
  `[-0.5563134, 1.3274549, -0.07586708, 0.5075991, -0.2171946, -0.7488514, -0.9092405, -0.6528551, 0.29621574]`
- **Euclidean Norm $\|q_0\|_2$:** `27.712810`
- **Sum of Coordinates $\sum q_i$:** `-16.196932`

---

## 5. Audit Conclusion

The discrepancy was caused by an unverified draft hash prefix (`f01297be...`) appearing in the Phase 4E.3 preflight planning text. 

The live execution script, experimental captures, output manifest, and existing Phase 3A artifact all use the exact, authoritative, and cryptographically verified vector whose SHA-256 hash is:

$$\mathbf{4a0428709013d77d8d284b369cb144734421bfdc4f6e4a83faf17db8114cf478}$$

