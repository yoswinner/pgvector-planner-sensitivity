# Phase 5C — IEEE A4 Manuscript Regeneration Package (`v2.2` / Manuscript `v1.3.3`)

**Project:** *How FP16 Vector Representation and TOAST Storage Layouts Shift Query Plan Selection in PostgreSQL: An Empirical and Cost-Model Study*  
**Author:** Yash Pradhan  
**Phase:** Phase 5C — Regenerate IEEE A4 Manuscript from V1.3.3  
**Candidate Status:** **`PHASE 5C — REGENERATED V1.3.3 FORMATTING CANDIDATE FOR INDEPENDENT REVIEW, PENDING AUTHOR CONFIRMATIONS`** (All original inputs, including `final_research_paper_source_v1.3.3.md`, `phase5c_scientific_manuscript_v1.3.3_changelog.md`, `ieee_a4_review_v2_1.zip`, and `conference-template-a4.docx`, are preserved unchanged.)

## 1. Authority & Input Provenance

| Input Artifact | Role & Authority | Size (Bytes) | Verified SHA-256 Hash | Modified? |
| :--- | :--- | :---: | :--- | :---: |
| `final_research_paper_source_v1.3.3.md` | **1. Sole Authoritative Scientific Source (`V1.3.3`)** | `131,397` | `fe5b75e85b5e093e5189af68b4498699921dd81fce29bac46873a6f84b4d4862` | **No (Unchanged)** |
| `phase5c_scientific_manuscript_v1.3.3_changelog.md` | **2. Approved V1.3.3 Scientific Changelog** | `2,372` | `6eb7d51499711f2b9d89cdd5a1835fc0958edba4633468e2abb75f55d76120e7` | **No (Unchanged)** |
| `ieee_a4_review_v2_1.zip` | **3. Accepted R4.4.1 Formatting & QA Baseline** | `9,579,531` | `e37baec01ee17eddc810019b10c28d255478892ab36ea30d9840f5c939d8e857` | **No (Unchanged)** |
| `conference-template-a4.docx` | **4. Original IEEE A4 Teacher Template** | `33,858` | `57e2125b0a04860e103fd634c2b5fd19a7ea571fa59ac577bd97afc73ad99482` | **No (Unchanged)** |
| `figures/figure_01.png` | 600 DPI Publication Figure 1 | `1,486,539` | `5c157ca923f5cd45ab4c0b4ad730b25a4632499f900db076d8c4ae9a2cf6a884` | **No (Unchanged)** |
| `figures/figure_02.png` | 600 DPI Publication Figure 2 | `1,400,750` | `cb6f1b9467f8d927e1242283714393c4c30ce6ae8d4a8e9ec596c217ad1cc59d` | **No (Unchanged)** |
| `figures/figure_03.png` | 600 DPI Publication Figure 3 | `912,447` | `796f1d96fbd80008410baa70a12f0185faac73e226e87de9b356c57811b19d23` | **No (Unchanged)** |

## 2. Package Contents (`ieee_a4_review_v2_2_v1.3.3/`)

All member sizes and SHA-256 hashes are recorded in `manifest_sha256.csv` and `SHA256SUMS.txt`:

1. **`final_research_paper_v1.3.3.docx`** — Regenerated IEEE A4 Word manuscript from `V1.3.3` (`3,591,305 B`, SHA-256: `e208f4c6c0949af90425878aaff9232617568396dc54c8677b27241b6e0a237b`).
2. **`final_research_paper_v1.3.3.pdf`** — Rendered 21-page IEEE A4 PDF manuscript via `LibreOffice 7.4.7.2` (`2,357,409 B`, SHA-256: `d2a5fe8589d1c66e01e74ddb87bfcd538d4cf7c3e430973e05864e2857487c9c`).
3. **`final_research_paper_source_v1.3.3.md`** — Authoritative V1.3.3 scientific Markdown source (`131,397 B`, SHA-256: `fe5b75e85b5e093e5189af68b4498699921dd81fce29bac46873a6f84b4d4862`).
4. **`phase5c_scientific_manuscript_v1.3.3_changelog.md`** — Approved V1.3.3 scientific changelog (`2,372 B`, SHA-256: `6eb7d51499711f2b9d89cdd5a1835fc0958edba4633468e2abb75f55d76120e7`).
5. **`phase5c_content_preservation_and_formatting_qa_report_v1.3.3.md`** — Complete Phase 5C content-preservation (`187` paragraphs, `980` cells, `11` equations, `241` distinct inline math expressions, `4/4` V1.3.3 scientific revisions) and 21-page visual formatting QA report.
6. **`phase5c_regeneration_changelog_v1.3.3.md`** — Concise Phase 5C regeneration changelog.
7. **`build_ieee_a4_manuscript_v2.py`** — Accepted R4.4.1 IEEE A4 DOCX/PDF generator script with CLI defaults updated to `v1.3.3` (`76,218 B`, SHA-256: `a347baf4cc71f13ac481cb23ac0df89e43f3b5eb512067c969a0ea0b6637a4e8`).
8. **`verify_ieee_a4_manuscript_v2.py`** — Portable 13-test verification suite (`test_01`–`test_13`) checking `final_research_paper_v1.3.3.docx` and `final_research_paper_v1.3.3.pdf` against `final_research_paper_source_v1.3.3.md` (`47,136 B`, SHA-256: `02a76bd5ffdd2bdef7b7f5cf4aa5d8505442ae2100773ca3ebeb586704467555`).
9. **`automated_test_log_v2_2_v1.3.3.txt`** — Captured execution output of `verify_ieee_a4_manuscript_v2.py` (`13 / 13` tests passed).
10. **`equation_and_math_verification_matrix_v2.md`** — Complete verification matrix for all 11 displayed equations and all 241 distinct inline math expressions (`557` occurrences).
11. **`conference-template-a4.docx`** — Unmodified original IEEE A4 template (`33,858 B`).
12. **`build_ieee_a4_manuscript.py`** & **`final_research_paper_source_v1.3.2.md`** — Preserved historical R4.2 script and V1.3.2 source for provenance traceability.
13. **`figures/figure_01.png`**, **`figures/figure_02.png`**, **`figures/figure_03.png`** — Unmodified 600 DPI publication figures.
14. **`manifest_sha256.csv`** & **`SHA256SUMS.txt`** — Complete file manifests and SHA-256 checksums.

## 3. Reproducible Build & Verification Commands

```bash
python3 -B build_ieee_a4_manuscript_v2.py \
  --template conference-template-a4.docx \
  --source final_research_paper_source_v1.3.3.md \
  --figures-dir figures \
  --output-docx final_research_paper_v1.3.3.docx \
  --output-pdf final_research_paper_v1.3.3.pdf \
  --modified-timestamp "2026-11-04T04:00:00Z"

python3 -B verify_ieee_a4_manuscript_v2.py
sha256sum -c SHA256SUMS.txt
```
