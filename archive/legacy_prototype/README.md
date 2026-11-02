# Legacy Prototype Archive

This directory contains early exploratory code, prototype test harnesses, and initial ingestion pipelines developed during Phase 1 and Phase 2 of this project.

---

## 1. Purpose and Historical Context

During the preliminary stages of research, these prototype scripts were used to:
- Test initial connections and table provisioning with Ollama and `pgvector`.
- Benchmark early end-to-end RAG ingestion pipelines with live embedding calls (`nomic-embed-text`).
- Run initial recall and latency sweeps comparing FP32 and FP16 embeddings.

These files have been superseded by the production research modules in `src/` and reproducible experiment scripts in `scripts/`. They are retained here in `archive/legacy_prototype/` for full methodological transparency and provenance auditability.

---

## 2. Directory Contents

### Prototype Source (`src/`)
- `benchmark.py`: Early end-to-end latency benchmark harness.
- `embeddings.py`: Ollama embedding client for `nomic-embed-text`.
- `hnsw_experiment.py`: Preliminary HNSW construction and search test harness.
- `ingestion.py`: Initial dataset streaming and batch ingestion pipeline.
- `preprocessing.py`: Character-based sliding window text chunking utility.
- `scale_experiment.py`: Early multi-scale benchmark script across 1k to 10k corpora.
- `search.py`: Basic cosine similarity query utility.

### Prototype Entrypoint
- `main.py`: Command-line driver for early exploratory runs.

### Prototype Tests (`tests/`)
- `test_basic.py`: Early connectivity and Ollama embedding smoke tests.
- `test_hnsw_experiment.py`: Unit tests for preliminary HNSW indexing routines.
- `test_ingestion_cache.py`: Unit tests for TSV caching and chunk validation.
- `test_representations.py`: Unit tests for vector representation conversion routines.
- `test_scale_experiment.py`: Unit tests for scale-experiment matrix generation.

---

## 3. Separation from Production Research Code

The production research codebase supporting Manuscript V1.3.2 is structured as follows:
- **Production Core**: Located in top-level `src/` (`planner_sensitivity_experiment.py`, `database.py`, `representations.py`, `config.py`).
- **Research Test Suite**: Located in top-level `tests/` (`test_planner_sensitivity_experiment.py`, `test_analysis_pipeline.py`, `conftest.py`). The default test suite executes 77 offline unit and regression tests in seconds without requiring Ollama or external services.
- **Experimental Execution & Verification**: Located in `scripts/` (`run_phase4e3_scale_sweep.py`, `run_phase4f1_exact_validation.py`, `generate_paper_figures.py`).

