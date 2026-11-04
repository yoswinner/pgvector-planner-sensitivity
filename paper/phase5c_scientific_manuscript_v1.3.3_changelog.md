# Scientific Manuscript Change Log — v1.3.3

Date: 2026-11-04

## Basis
This revision applies the four author-approved, evidence-boundary corrections agreed after closure of Phase 5A and Phase 5B. It is derived from the v1.3.2 scientific Markdown source. The original v1.3.2 package and all R4.4.1 formatting artifacts remain preserved and unchanged.

## Changes
1. **Reproduction scope (Section VI, limitation 7):** Replaced the unqualified “100% offline reproduction” claim with a bounded statement covering post-collection analyses reproduced from preserved evidence, explicitly distinguishing this from full from-scratch corpus construction, embedding generation, and original database-state reconstruction.
2. **Embedding provenance (Section IV-A):** Clarified that `nomic-embed-text:latest` is a mutable Ollama model tag and that the exact model artifact digest and Ollama runtime build were not recorded.
3. **HNSW construction variability (Section VI, limitation 3):** Removed the unsupported assertion that the observed 0.005 recall differences lie within single-graph construction variance. The revised text states that repeated graph builds were not evaluated and the contribution of graph-construction variability cannot be isolated.
4. **Latency repeatability (Section VI, limitation 2):** Added that the reported latency measurements characterize observed runs and that consistency across independent reruns was not established.

## Explicitly unchanged
- Experimental measurements, query results, statistical values, tables, figures, equations, references, and benchmark configuration.
- The upstream dataset-selector and dependency-lockfile disclosures, which were already present.
- The original v1.3.2 Markdown, DOCX, PDF, ZIP package, and R4.4.1 formatting candidate.

## Verification
- Source basis: `final_research_paper_source_v1.3.2.md` from `phase4i_ieee_final_draft_v1.3.2 (2)(1).zip`.
- Original source SHA-256: `8d3b670a9320fe429c9e4fab4f1981afe4a505404a7e437101ffce95f9d5ab4f`.
- Four targeted textual corrections applied; assertions confirmed each replacement occurs once.
- No benchmark rerun, source-repository modification, Git operation, database operation, or Ollama operation was performed.
- This is a **scientific-source revision only**. It is not yet a regenerated or accepted DOCX/PDF, and is not the final submission package.
