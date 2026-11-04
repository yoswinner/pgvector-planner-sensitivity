# Dataset Acquisition, Provenance, and Licensing Guide

This document describes the upstream provenance, licensing framework, acquisition procedures, determinism properties, and byte-level checksums for the textual corpus and query vectors used in this research.

---

## 1. Upstream Data Source and Licensing Framework

The textual passages used to evaluate vector storage layouts and PostgreSQL planner sensitivity originate from the **MS MARCO (Microsoft Machine Reading Comprehension)** passage ranking collection via the BeIR benchmark distribution:
- **Upstream Distribution**: [`BeIR/msmarco`](https://huggingface.co/datasets/BeIR/msmarco) (Hugging Face Datasets)
- **Configuration**: `corpus`
- **Split**: `corpus`
- **Original Source**: Microsoft Corporation ([MS MARCO Project Page & Terms](https://microsoft.github.io/msmarco/))

### 1.1 Distinct Intellectual Property and Licensing Considerations
The research involves distinct intellectual property and licensing layers that must be carefully distinguished:

1. **Upstream Dataset Terms (Microsoft MS MARCO)**:
   - The MS MARCO dataset was released by Microsoft Corporation under the **[MS MARCO Terms of Use (Non-Commercial Research Use Agreement)](https://microsoft.github.io/msmarco/)**.
   - Under these terms, Microsoft provides the dataset for intended non-commercial research use, with no licence or other intellectual-property rights granted over the underlying dataset or third-party web content.
2. **BeIR Repository Licence Declaration**:
   - The Hugging Face repository for [`BeIR/msmarco`](https://huggingface.co/datasets/BeIR/msmarco) declares `cc-by-sa-4.0` in its repository licence metadata.
   - This repository declaration does not independently establish rights to redistribute underlying MS MARCO passages or third-party web content.
3. **Underlying Third-Party Web Content Rights**:
   - The textual passages extracted from web pages and search results remain subject to the copyrights and intellectual property rights of the respective original content authors and web publishers.
4. **Project Code and Documentation Licence (Apache 2.0)**:
   - The **[Apache License, Version 2.0](../LICENSE)** in this repository applies strictly and exclusively to the original research software, experiment harnesses, analysis pipelines, test suites, and documentation authored for this study.
   - It does not apply to MS MARCO passages, BeIR dataset content, or third-party dependencies, nor does it grant licences over third-party corpus content.

### 1.2 Repository Redistribution Policy
To adhere strictly to copyright boundaries, upstream terms of use, and conservative open-science practices:
- **No Raw or Chunked Passage Text is Bundled in this Public Repository:** The repository does not redistribute `msmarco_10k_canonical.tsv` or derived raw text chunks. Only structural metadata ([`data/raw/msmarco_10k_canonical.meta.json`](../data/raw/msmarco_10k_canonical.meta.json)) is bundled.
- **Self-Contained Scientific Verification:** All empirical benchmark findings, statistical tests, cost-model proofs, and publication figures in this repository can be fully reproduced offline without downloading or processing raw passage text, using the curated summaries and plan captures in `results/planner_sensitivity/`.
- **Downstream Corpus Acquisition:** Researchers wishing to perform upstream corpus reconstruction (Level 3) must acquire the data directly from the upstream distribution ([`BeIR/msmarco`](https://huggingface.co/datasets/BeIR/msmarco)) under its applicable terms.

*(Note: This overview provides factual provenance and documentation of licensing context; it does not constitute formal legal counsel).*

---

## 2. Canonical Corpus Specifications and Byte-Level Line-Ending Analysis

The raw corpus file `msmarco_10k_canonical.tsv` contains document-level passage records streamed from `BeIR/msmarco`. Chunking is applied downstream during table ingestion. The file satisfies the following exact specifications (recorded in `data/raw/msmarco_10k_canonical.meta.json`):

| Property | Canonical Specification | Notes & Validation |
| :--- | :--- | :--- |
| **Upstream Identifier** | `BeIR/msmarco` (`corpus` split) | Hugging Face streaming dataset |
| **Total TSV Document Records** | **5,457 records** | Exactly one line per source document |
| **TSV Format** | `doc_id \t document_text` | Two tab-separated fields per line |
| **Line Terminator Count** | **5,457 CRLF (`\r\n`) terminators** | 0 bare LF (`\n`), 0 bare CR (`\r`) |
| **Physical File Size (Windows CRLF)** | **1,757,907 bytes** | Generated on Windows 11 benchmark host |
| **Physical SHA-256 (Windows CRLF)** | **`45c681d1573b83f469e8b71c7f74d587e48285f58561d2eb4c865293db650cd2`** | Actual on-disk authority |
| **Normalized File Size (Unix/POSIX LF)** | **1,752,450 bytes** | Exactly $1{,}757{,}907 - 5{,}457$ bytes |
| **Normalized SHA-256 (Unix/POSIX LF)** | **`cdca54aa145a8343916447f9b9fcd8ddcfdb72a3129c5263f5fba3c485434e8b`** | Matches `msmarco_10k_canonical.meta.json` |
| **Downstream Chunks Produced** | **10,001 chunks** | Character sliding window (size=300, overlap=50) |

### Checksum & Line-Ending Proof
The file `msmarco_10k_canonical.tsv` contains exactly 5,457 records, each terminated by a standard Windows two-byte sequence `\r\n` (CRLF), yielding 1,757,907 bytes. When converting every `\r\n` sequence to `\n` (LF), exactly 5,457 carriage-return bytes are removed, resulting in:
$$1{,}757{,}907 - 5{,}457 = 1{,}752{,}450\text{ bytes}$$
The SHA-256 of this normalized byte stream is `cdca54aa...`, which matches the recorded metadata hash in `msmarco_10k_canonical.meta.json` to the bit. Both checksums represent the identical sequence of 5,457 documents and yield the exact same 10,001 chunks upon applying `chunk_text(text, chunk_size=300, overlap=50)`.

---

## 3. Query Vector Registry & $q_0$ Provenance

The 20 canonical evaluation query vectors ($q_0 \dots q_{19}$) used throughout the benchmark are bundled in:  
`results/planner_sensitivity/phase3_tie_sensitivity_20261031/recovered_query_vectors.csv`

### 3.1 Canonical Query $q_0$ Natural-Language Identity
The primary benchmark query $q_0$ (`query_id = 0`) has the following natural-language text:
$$\mathbf{"what\ was\ the\ purpose\ of\ the\ manhattan\ project"}$$

- **Harness Definition:** Pinned at line 14 of [`../src/representations.py`](../src/representations.py) (`EVALUATION_QUERIES[0]`) under Git commit `3f2beee66cecd67aa8fc4cec69c364b92c07b884`.
- **Text UTF-8 SHA-256:** `788468a7d6b628cbd6ecc08161843a548791e7dcda15d670f9f95a1fbddbaa84`
- **Corpus Retrieval Validation:** When executed against the canonical corpus, $q_0$ retrieves Chunk IDs `[11, 4, 5, 14, 3, 10, 12, 9, 1, 7]` in rank order 1..10 (recorded in `results/planner_sensitivity/phase3a_evidence_addendum_20261031/fp32_reference_top10_ids.csv`). Inspection of `msmarco_10k_canonical.tsv` confirms that every one of these retrieved chunks is a historical passage detailing the Manhattan Project and atomic weapons development.
- **Resolution of "Routing" Narrative Error:** An unverified narrative draft in Phase 4E.3 (`q0_hash_reconciliation.md`) mistakenly attributed $q_0$ to `"what is routing in computer networks"`. As formally audited and confirmed in Phase 4F.1.1 (`paper/phase4f1_targeted_verification_report.md`) and in Manuscript V1.3.2 Section IV-B, that attribution was an informal narrative error. The true query has always been `"what was the purpose of the manhattan project"`. The underlying floating-point vector coordinates and cryptographic hashes never changed.

### 3.2 Canonical Query $q_0$ Vector Fingerprints
The precomputed 768-dimensional float coordinates for $q_0$ satisfy:

- **Vector Dimension:** 768 dimensions (IEEE-754 single precision)
- **Authoritative JSON String (UTF-8) SHA-256:**  
  **`4a0428709013d77d8d284b369cb144734421bfdc4f6e4a83faf17db8114cf478`**  
  *(Exact string representation `json.dumps(vec_floats)` stored in `recovered_query_vectors.csv` and asserted by `scripts/run_phase4e3_scale_sweep.py`).*
- **Raw Float32 Little-Endian Binary Array (`<768f`, 3,072 bytes) SHA-256:**  
  **`3f5a10a6816f561587d427c56c11ec08586b587690262df8a8060150341969dd`**
- **Raw Float32 Big-Endian Binary Array (`>768f`, 3,072 bytes) SHA-256:**  
  **`2f7189871d386032ba483219018cb00b71d77e5947975780355f379b1e77b498`**
- **Euclidean Norm $\|q_0\|_2$:** `27.712810` (unnormalized)
- **Sum of Coordinates $\sum q_i$:** `-16.196932`

> **Reconciliation of Draft Prefix `f01297be...`**: An earlier preflight planning document referenced a hash prefix beginning `f01297be...`. As established in `results/planner_sensitivity/scale_sweep_plan_only/q0_hash_reconciliation.md`, that string was an unverified draft placeholder from narrative planning. It does not correspond to any valid serialization. The authoritative vector across all execution phases has always been `4a042870...`.

---

## 4. Scope of Included Data vs. Live Execution Requirements

To prevent ambiguity about what this repository supplies:

1. **What is Supplied in the Repository:**
   - The 20 canonical evaluation query vectors ($q_0 \dots q_{19}$) in `recovered_query_vectors.csv`.
   - The 486-cell analytical sequential scan formula validation dataset (`seq_cost_formula_validation.csv`).
   - The 18-scale summary and storage metrics from the 972-plan sweep (`scale_sweep_summary.csv`, `scale_sweep_storage.csv`).
   - All Phase 2 latency summaries, storage measurements, and boundary-tie statistics in `results/planner_sensitivity/`.
2. **What is NOT Supplied in the Repository:**
   - The raw MS MARCO passage text (excluded due to licensing constraints).
   - The complete set of 10,001 document corpus vector embeddings (~30 MB uncompressed float arrays).
3. **Implications for Reproduction:**
   - **Level 1 (Offline Statistical & Visual Reproduction):** Fully self-contained. Runs immediately in ~3 seconds using the supplied CSV and JSON evidence.
   - **Level 2 (Live PostgreSQL Plan Sweeps & Cost Verification):** Requires a running PostgreSQL instance that has already been provisioned with the experimental scale tables in `compression_aware_rag_exp` and `compression_aware_rag_scale`, or access to the complete corpus embeddings. The repository's 20 query vectors alone cannot populate corpus tables.
   - **Level 3 (Full End-to-End Re-Ingestion & Embedding):** Requires downloading the raw corpus from Hugging Face and generating embeddings via Ollama.

---

## 5. Dataset Acquisition & Determinism Limitations

For researchers seeking to execute Level 3 (complete from-scratch corpus acquisition and embedding generation):

### 5.1 Acquisition Script
Matching `archive/legacy_prototype/src/ingestion.py`:
```python
import os
import csv
from datasets import load_dataset
from archive.legacy_prototype.src.preprocessing import chunk_text

output_path = "data/raw/msmarco_10k_canonical.tsv"
os.makedirs("data/raw", exist_ok=True)

print("Streaming BeIR/msmarco corpus from Hugging Face...")
ds = load_dataset("BeIR/msmarco", "corpus", split="corpus", streaming=True)

doc_count = 0
total_chunks = 0
target_chunks = 10000

with open(output_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    for item in ds:
        doc_id = str(item.get("_id", "")).strip()
        text = item.get("text", "").strip()
        if not doc_id or not text:
            continue

        chunks = chunk_text(text, chunk_size=300, overlap=50)
        if not chunks:
            continue

        writer.writerow([doc_id, text])
        doc_count += 1
        total_chunks += len(chunks)

        if total_chunks >= target_chunks:
            break

print(f"Caching complete: {doc_count} documents yielding {total_chunks} chunks saved to {output_path}.")
```

### 5.2 Verification
```bash
# On Windows (PowerShell)
Get-FileHash data/raw/msmarco_10k_canonical.tsv -Algorithm SHA256
# Expected Windows CRLF: 45c681d1573b83f469e8b71c7f74d587e48285f58561d2eb4c865293db650cd2

# On Linux/macOS
sha256sum data/raw/msmarco_10k_canonical.tsv
# Expected Unix LF:     cdca54aa145a8343916447f9b9fcd8ddcfdb72a3129c5263f5fba3c485434e8b
```

### 5.3 Known Determinism Limitations
When reconstructing the dataset from scratch via Level 3, be aware of the following historical provenance characteristics:

1. **Hugging Face Dataset Revision**: `msmarco_10k_canonical.meta.json` records the snapshot timestamp (`2026-10-14T07:24:04Z`), but does not record an immutable Git commit hash for the `BeIR/msmarco` repository. Upstream repository modifications could alter streaming shard order.
2. **Datasets Library Version**: The exact library version of Hugging Face `datasets` used during initial ingest was not pinned in metadata.
3. **Document Selection Order**: Selection streams documents in the default iteration order of the streaming iterator until 10,001 chunks are reached.
4. **Embedding Model Tag Mutability**: The original embedding pipeline used the Ollama tag `nomic-embed-text:latest` without recording the underlying 256-bit manifest digest. Upstream model checkpoint updates under the `:latest` tag could introduce floating-point variations.
5. **Embedding Parameters**: Embeddings were generated with 768 dimensions using Ollama's default `/api/embeddings` endpoint with the raw chunk text as prompt, without task-specific instruction prefixes.
