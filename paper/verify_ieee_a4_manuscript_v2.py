#!/usr/bin/env python3
r"""
Phase R4.4.1 — Automated Verification and Acceptance Test Suite
===============================================================
Executes 12 comprehensive test methods (covering all 16 Phase R4.4 acceptance gates
plus Phase R4.4.1 QA audit corrections) against `build_ieee_a4_manuscript_v2.py`,
`research_paper_ieee_a4_v2.docx`, `research_paper_ieee_a4_v2.pdf`, and the
authoritative provenance inputs using portable relative paths.
"""

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile

import docx
import lxml.etree as ET
import pypdf
import pypdfium2 as pdfium

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ieee_a4_manuscript_v2 as gen_v2


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_portable_path(filename: str, subdirs=("", "v132_ref", "figures", "figures_v3", "out_v2")) -> str:
    """Resolve `filename` portably relative to this script's directory or its parent directory."""
    here = os.path.dirname(os.path.abspath(__file__))
    parent = os.path.dirname(here)
    env_ext = os.environ.get("R44_EXTERNAL_DIR", "")
    search_roots = [here, parent]
    if env_ext:
        search_roots.append(env_ext)
    for root in search_roots:
        for sub in subdirs:
            cand = os.path.join(root, sub, filename) if sub else os.path.join(root, filename)
            if os.path.exists(cand):
                return cand
    return os.path.join(here, filename)


class PhaseR44VerificationSuite(unittest.TestCase):
    """Comprehensive automated test suite for Phase R4.4.1 generator v2 and candidate outputs."""

    HERE = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_DOCX = resolve_portable_path("conference-template-a4.docx")
    ORIG_GEN_PY = resolve_portable_path("build_ieee_a4_manuscript.py")
    SOURCE_MD = resolve_portable_path("final_research_paper_source_v1.3.3.md")
    SOURCE_MD_V132 = resolve_portable_path("final_research_paper_source_v1.3.2.md")
    CHANGELOG_V133 = resolve_portable_path("phase5c_scientific_manuscript_v1.3.3_changelog.md")
    FIGURES_DIR = (
        os.path.join(HERE, "figures")
        if os.path.isdir(os.path.join(HERE, "figures"))
        else os.path.dirname(resolve_portable_path("figure_01.png"))
    )
    OUT_DOCX = resolve_portable_path("final_research_paper_v1.3.3.docx")
    OUT_PDF = resolve_portable_path("final_research_paper_v1.3.3.pdf")

    @classmethod
    def setUpClass(cls):
        with open(cls.SOURCE_MD, "r", encoding="utf-8") as f:
            cls.md_text = f.read()
        cls.md_lines = [line.rstrip("\r\n") for line in cls.md_text.splitlines()]
        cls.doc = docx.Document(cls.OUT_DOCX)
        cls.pdf_reader = pypdf.PdfReader(cls.OUT_PDF)
        cls.pdf_text = subprocess.check_output(["pdftotext", cls.OUT_PDF, "-"]).decode("utf-8")

    def test_01_input_and_provenance_hashes(self):
        """Gate 1, 2, 3: Verify exact SHA-256 hashes of all 6 bundled provenance inputs and log external archive checks."""
        required_local = {
            "conference-template-a4.docx": (
                self.TEMPLATE_DOCX,
                "57e2125b0a04860e103fd634c2b5fd19a7ea571fa59ac577bd97afc73ad99482",
            ),
            "build_ieee_a4_manuscript.py": (
                self.ORIG_GEN_PY,
                "15868837ad1b0a907ee32f24c278d9bf9a317d33abe4bf2c428afc7eb2ba50f4",
            ),
            "final_research_paper_source_v1.3.3.md": (
                self.SOURCE_MD,
                "fe5b75e85b5e093e5189af68b4498699921dd81fce29bac46873a6f84b4d4862",
            ),
            "phase5c_scientific_manuscript_v1.3.3_changelog.md": (
                self.CHANGELOG_V133,
                "6eb7d51499711f2b9d89cdd5a1835fc0958edba4633468e2abb75f55d76120e7",
            ),
            "final_research_paper_source_v1.3.2.md": (
                self.SOURCE_MD_V132,
                "8d3b670a9320fe429c9e4fab4f1981afe4a505404a7e437101ffce95f9d5ab4f",
            ),
            "figures/figure_01.png": (
                os.path.join(self.FIGURES_DIR, "figure_01.png"),
                "5c157ca923f5cd45ab4c0b4ad730b25a4632499f900db076d8c4ae9a2cf6a884",
            ),
            "figures/figure_02.png": (
                os.path.join(self.FIGURES_DIR, "figure_02.png"),
                "cb6f1b9467f8d927e1242283714393c4c30ce6ae8d4a8e9ec596c217ad1cc59d",
            ),
            "figures/figure_03.png": (
                os.path.join(self.FIGURES_DIR, "figure_03.png"),
                "796f1d96fbd80008410baa70a12f0185faac73e226e87de9b356c57811b19d23",
            ),
        }
        for label, (path, exp_hash) in required_local.items():
            self.assertTrue(os.path.isfile(path), f"Missing required provenance input ({label}): {path}")
            self.assertEqual(sha256_file(path), exp_hash, f"SHA-256 mismatch on required input {label}")

        optional_external = {
            "phase4i_ieee_final_draft_v1.3.2.zip": "b1cf115058dcd37697856e5dcc7e635e9f9dae1c458ad72fae4ee581b9733dbe",
            "ieee_a4_review_v1.zip": "299b029aae9f404c2275374bc703cbbcf083bfb631b3f64234bd3684dff73858",
            "ieee_a4_review_v2.zip": "b2a462bd820413481d680d974f7a2cb724d43dcbbfea778e2f4c059f174dcc91",
        }
        verified_ext = []
        skipped_ext = []
        for ext_name, exp_hash in optional_external.items():
            ext_path = resolve_portable_path(ext_name)
            if os.path.isfile(ext_path):
                self.assertEqual(sha256_file(ext_path), exp_hash, f"SHA-256 mismatch on external archive {ext_name}")
                verified_ext.append(ext_name)
            else:
                skipped_ext.append(ext_name)
        print(
            f"\n  [test_01] Verified {len(required_local)}/{len(required_local)} bundled provenance inputs; "
            f"external archives verified={verified_ext}, standalone-skipped={skipped_ext}"
        )

    def test_02_inline_markdown_parser_unit_tests(self):
        """Gate 6: Positive and negative unit tests for recursive inline Markdown and math parser."""
        # 1. Nested code with literal asterisk inside bold (Table I R6C0 & R13C0 case)
        ast1 = gen_v2.parse_inline_ast("**Index total cost (`*indexTotalCost`)**")
        self.assertEqual(
            ast1,
            [("BOLD", [("TEXT", "Index total cost ("), ("CODE", "*indexTotalCost"), ("TEXT", ")")])],
        )

        # 2. Literal $1 inside code span alongside inline math $K$ (Section I L17 case)
        ast2 = gen_v2.parse_inline_ast("top-$K$ query (`ORDER BY embedding <=> $1 LIMIT K`) and top-$K$ sort")
        self.assertEqual(
            ast2,
            [
                ("TEXT", "top-"),
                ("MATH", "K"),
                ("TEXT", " query ("),
                ("CODE", "ORDER BY embedding <=> $1 LIMIT K"),
                ("TEXT", ") and top-"),
                ("MATH", "K"),
                ("TEXT", " sort"),
            ],
        )

        # 3. Bold with trailing table-note reference asterisk (Sub-Table III-B R6C6 case)
        ast3 = gen_v2.parse_inline_ast("**Significant (Exploratory)***")
        self.assertEqual(
            ast3,
            [("BOLD", [("TEXT", "Significant (Exploratory)")]), ("TEXT", "*")],
        )

        # 4. Escaped delimiters outside code/math (\*, \$, \_, \{, \})
        ast4 = gen_v2.parse_inline_ast(r"\*Note: literal \$100 and \_ and \{a\}")
        self.assertEqual(ast4, [("TEXT", "*Note: literal $100 and _ and {a}")])

        # 5. Outer italic wrapping nested bold, code with *, and inline math (Figure 2/3 caption case)
        ast5 = gen_v2.parse_inline_ast("*Caption with **[1]** and `1.0000*` at $\\tau = 10^{-5}$*")
        self.assertEqual(
            ast5,
            [
                (
                    "ITALIC",
                    [
                        ("TEXT", "Caption with "),
                        ("BOLD", [("TEXT", "[1]")]),
                        ("TEXT", " and "),
                        ("CODE", "1.0000*"),
                        ("TEXT", " at "),
                        ("MATH", r"\tau = 10^{-5}"),
                    ],
                )
            ],
        )

        # 6. Negative test: malformed / unmatched delimiters must never drop text silently
        malformed = "Unmatched `backtick and *single asterisk and **double asterisk and $dollar end"
        tmp_doc = docx.Document()
        p = tmp_doc.add_paragraph()
        gen_v2.add_formatted_runs(p, malformed)
        self.assertEqual(p.text, malformed)

    def test_03_displayed_and_inline_math_fidelity(self):
        """Gate 5: Verify all 11 displayed equations and all 241 distinct inline math expressions (557 occurrences)."""
        # Check styles.xml equation font
        with zipfile.ZipFile(self.OUT_DOCX, "r") as z:
            styles_root = ET.fromstring(z.read("word/styles.xml"))
            doc_root = ET.fromstring(z.read("word/document.xml"))

        eq_styles = styles_root.xpath("//*[local-name()='style' and @*[local-name()='styleId']='equation']")
        self.assertEqual(len(eq_styles), 1)
        rfonts = eq_styles[0].xpath(".//*[local-name()='rFonts']")
        self.assertEqual(len(rfonts), 1)
        for attr in ("ascii", "hAnsi", "cs"):
            self.assertEqual(
                rfonts[0].get(f"{{{gen_v2.W_NS}}}{attr}"),
                "Times New Roman",
                f"equation style {attr} font is not Times New Roman",
            )

        # Verify all 11 displayed equation paragraphs in DOCX
        eq_paras = [p for p in self.doc.paragraphs if p.style.name == "equation"]
        self.assertEqual(len(eq_paras), 11, f"Expected 11 displayed equations, found {len(eq_paras)}")

        expected_substrings = [
            "TOAST_TUPLE_THRESHOLD = MaximumBytesPerTuple(4)",
            "costs.indexTotalCost = numIndexPages · spc_random_page_cost",
            "candidateTuples(N) = entryLevel(N) · m",
            "indexStartupCostinitial = costs.indexTotalCost · ratio",
            "indexStartupCostinitial, FP32 = 1996.0 × 0.40572022",
            "indexStartupCostinitial, FP16 = 1000.0 × 0.40572022",
            "Δ = startupPages · (random_page_cost - seq_page_cost)",
            "indexStartupCostadjusted = relpages · seq_page_cost",
            "IndexScanrun = (indexTotalCost - IndexScanstartup)",
            "Limittotal, HNSW = IndexScanstartup + (K / N) · IndexScanrun",
            "Limittotal, Seq = relpages · seq_page_cost",
        ]
        for idx, (ep, exp_sub) in enumerate(zip(eq_paras, expected_substrings), 1):
            self.assertIn(exp_sub, ep.text, f"Equation {idx} mismatch: {ep.text}")
            for r in ep.runs:
                self.assertIn(r.font.name, ("Times New Roman", "Consolas"))

        # Extract and verify all 241 distinct inline math expressions (557 total occurrences) from source Markdown
        md_no_disp = re.sub(r"\$\$[\s\S]*?\$\$", "", self.md_text)
        md_no_code = re.sub(r"`[^`\n]+`", "", md_no_disp)
        inline_math_occurrences = re.findall(r"(?<!\\)\$([^\$\n]+?)(?<!\\)\$", md_no_code)
        distinct_inline_maths = sorted(set(inline_math_occurrences))
        self.assertEqual(len(inline_math_occurrences), 557, "Expected 557 inline math occurrences in source Markdown")
        self.assertEqual(len(distinct_inline_maths), 241, "Expected 241 distinct inline math expressions in source Markdown")

        all_docx_text = "\n".join(p.text for p in self.doc.paragraphs) + "\n" + "\n".join(
            c.text for tbl in self.doc.tables for row in tbl.rows for c in row.cells
        )
        tmp_doc = docx.Document()
        for expr in distinct_inline_maths:
            p_m = tmp_doc.add_paragraph()
            gen_v2.add_formatted_runs(p_m, f"${expr}$")
            rendered = p_m.text
            self.assertNotIn("\\", rendered, f"Raw LaTeX backslash leaked in inline math {expr!r} -> {rendered!r}")
            if "{" in rendered or "}" in rendered:
                self.assertTrue(
                    r"\{" in expr or r"\}" in expr,
                    f"Unescaped LaTeX brace leaked in inline math {expr!r} -> {rendered!r}",
                )
            self.assertIn(
                rendered,
                all_docx_text,
                f"Rendered inline math {rendered!r} (from {expr!r}) missing from generated DOCX",
            )

        # Verify subscript and superscript vertAlign elements exist in word/document.xml
        subs = doc_root.xpath("//*[local-name()='vertAlign' and @*[local-name()='val']='subscript']")
        sups = doc_root.xpath("//*[local-name()='vertAlign' and @*[local-name()='val']='superscript']")
        self.assertEqual(len(subs), 129, "Expected 129 subscript runs across equations, body, and tables")
        self.assertGreater(len(sups), 40, "Expected >40 superscript runs across equations, body, and tables")

        # Verify specific mathematical symbols in rendered PDF text
        for sym in ["⌊", "⌋", "⌈", "⌉", "Δ", "τ", "α", "χ", "ϵ", "≤", "≥", "∈", "⊆", "∩", "×", "·", "±", "≈", "√(20)", "C(28, 2) = 378", "L\u0304", "L\u0303"]:
            self.assertIn(sym, self.pdf_text, f"Mathematical symbol/construct {repr(sym)} missing from PDF text")

    def test_04_zero_delimiter_leakage(self):
        """Gate 6: Confirm zero leaked Markdown or LaTeX delimiters in all paragraphs and table cells."""
        for idx, p in enumerate(self.doc.paragraphs):
            t = p.text
            self.assertNotIn("`", t, f"Backtick leaked in P[{idx}]: {t[:100]}")
            self.assertNotIn("**", t, f"Double-asterisk leaked in P[{idx}]: {t[:100]}")
            self.assertNotIn("\\text", t, f"\\text leaked in P[{idx}]: {t[:100]}")
            self.assertNotIn("\\binom", t, f"\\binom leaked in P[{idx}]: {t[:100]}")
            self.assertNotIn("\\epsilon", t, f"\\epsilon leaked in P[{idx}]: {t[:100]}")
            self.assertNotIn("\\Note", t, f"\\Note leaked in P[{idx}]: {t[:100]}")
            # Allow literal PostgreSQL parameter $1 only
            t_no_param = t.replace("$1", "")
            self.assertNotIn("$", t_no_param, f"Dollar sign leaked in P[{idx}]: {t[:100]}")

        total_cells = 0
        for t_idx, tbl in enumerate(self.doc.tables):
            for r_idx, row in enumerate(tbl.rows):
                for c_idx, cell in enumerate(row.cells):
                    total_cells += 1
                    ct = cell.text
                    self.assertNotIn("`", ct, f"Backtick leaked in Table[{t_idx}] R{r_idx}C{c_idx}: {ct}")
                    self.assertNotIn("**", ct, f"Double-asterisk leaked in Table[{t_idx}] R{r_idx}C{c_idx}: {ct}")
                    self.assertNotIn("$", ct, f"Dollar sign leaked in Table[{t_idx}] R{r_idx}C{c_idx}: {ct}")
                    self.assertNotIn("\\", ct, f"Backslash leaked in Table[{t_idx}] R{r_idx}C{c_idx}: {ct}")
        self.assertEqual(total_cells, 980, f"Expected 980 total cells across 9 tables, found {total_cells}")

    def test_05_numbering_and_hierarchy(self):
        """Gate 7: Verify section, subsection, figure, table, footnote, and reference numbering in DOCX & PDF."""
        h1_texts = [p.text for p in self.doc.paragraphs if p.style.name == "Heading 1"]
        self.assertEqual(
            h1_texts,
            [
                "Introduction",
                "Background and Source-Level Cost-Model Analysis",
                "Related Work",
                "Experimental Methodology",
                "Empirical Results",
                "Discussion, Dimensionality Regimes, Practical Guidelines, and Limitations",
                "Conclusion",
            ],
        )
        h5_texts = [p.text for p in self.doc.paragraphs if p.style.name == "Heading 5"]
        self.assertEqual(
            h5_texts,
            [
                "Appendix A: Secondary Analysis — Retrieval Boundary Ties, Exact Vector-Equality Cluster, and τ-Tolerance Sensitivity",
                "Acknowledgment",
                "References",
            ],
        )
        h2_texts = [p.text for p in self.doc.paragraphs if p.style.name == "Heading 2"]
        self.assertEqual(len(h2_texts), 14)
        for h2 in h2_texts:
            self.assertFalse(re.match(r"^[A-Z]\.\s+", h2), f"Redundant letter prefix in Heading 2: {h2}")

        # Verify rendered PDF text has single numbering and zero doubled numbering
        for bad_pat in ["I. I.", "II. II.", "A. A.", "B. B.", "Fig. 1. Fig. 1.", "Fig. 2. Fig. 2.", "Fig. 3. Fig. 3.", "[1] [1]", "TABLE IV.\nTABLE II-C", "\\Note:"]:
            self.assertNotIn(bad_pat, self.pdf_text, f"Doubled/corrupted numbering {repr(bad_pat)} found in PDF")

        for good_pat in ["I. INTRODUCTION", "II. BACKGROUND", "III. RELATED WORK", "IV. EXPERIMENTAL METHODOLOGY", "V. EMPIRICAL RESULTS", "VI. DISCUSSION", "VII. CONCLUSION", "Fig. 1. PostgreSQL 18.4", "Fig. 2. Unforced Planner", "Fig. 3. Query-Level Retrieval"]:
            self.assertIn(good_pat, self.pdf_text, f"Expected numbered heading/caption {repr(good_pat)} missing from PDF")

    def test_06_tables_footnotes_and_group_headers(self):
        """Gate 8: Verify all 9 tables, Sub-Table III-A separation, Table I group rows, and all 8 table notes."""
        self.assertEqual(len(self.doc.tables), 9)
        expected_shapes = [
            (24, 5),   # Table I
            (10, 13),  # Table II
            (19, 7),   # Table II-B
            (19, 8),   # Table II-C
            (10, 7),   # Sub-Table III-A
            (7, 7),    # Sub-Table III-B
            (10, 10),  # Sub-Table III-C
            (6, 6),    # Table V
            (19, 10),  # Table IV
        ]
        for idx, (tbl, exp_shape) in enumerate(zip(self.doc.tables, expected_shapes)):
            actual_shape = (len(tbl.rows), len(tbl.columns))
            self.assertEqual(actual_shape, exp_shape, f"Table[{idx}] shape {actual_shape} != {exp_shape}")

        # Check Table III and Sub-Table III-A are distinct `table head` paragraphs
        tbl_heads = [p.text for p in self.doc.paragraphs if p.style.name == "table head"]
        self.assertEqual(len(tbl_heads), 10, f"Expected 10 table head paragraphs (TABLE III + 9 tables), found {len(tbl_heads)}")
        self.assertTrue(any(th.startswith("TABLE III. Non-Parametric") and "Sub-Table III-A" not in th for th in tbl_heads))
        self.assertTrue(any(th.startswith("Sub-Table III-A: Tie-Corrected Friedman") for th in tbl_heads))

        # Check all 8 table footnotes start cleanly with `*Note:` or `*At N = 850`
        tbl_notes = [p.text for p in self.doc.paragraphs if p.style.name == "table footnote"]
        self.assertEqual(len(tbl_notes), 8)
        for tn in tbl_notes:
            self.assertTrue(tn.startswith("*Note:") or tn.startswith("*At N = 850"), f"Malformed table note prefix: {tn[:60]}")
            self.assertFalse(tn.endswith("*"), f"Trailing asterisk left on table note: {tn[-40:]}")

    def test_07_dynamic_abstract_and_keywords(self):
        """Gate 9: Confirm Abstract (247 words) and Keywords are dynamically parsed from the canonical Markdown source."""
        abs_paras = [p for p in self.doc.paragraphs if p.style.name == "Abstract"]
        kw_paras = [p for p in self.doc.paragraphs if p.style.name == "Keywords"]
        self.assertEqual(len(abs_paras), 1)
        self.assertEqual(len(kw_paras), 1)
        self.assertTrue(abs_paras[0].text.startswith("Abstract—PostgreSQL extensions such as pgvector"))
        self.assertTrue(abs_paras[0].text.endswith("(0.985, 0.955, and 0.930 for fp32_plain)."))
        # Verify exact 247-word whitespace word count on Abstract
        self.assertEqual(len(abs_paras[0].text.split()), 247, "Expected 247 whitespace-delimited words in Abstract")
        self.assertEqual(
            kw_paras[0].text,
            "Keywords—PostgreSQL, pgvector, query optimization, HNSW indexing, TOAST storage, half-precision floating-point (FP16).",
        )

        # Dynamic fixture test: modify Abstract & Keywords in a temporary Markdown copy and verify output updates
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_md = os.path.join(tmpdir, "mod_source.md")
            mod_docx = os.path.join(tmpdir, "mod_out.docx")
            custom_text = self.md_text.replace(
                "**Abstract**—PostgreSQL extensions",
                "**Abstract**—DYNAMIC_ABSTRACT_SENTINEL_CHECK PostgreSQL extensions",
                1,
            ).replace(
                "*Keywords*—PostgreSQL,",
                "*Keywords*—DYNAMIC_KEYWORD_SENTINEL, PostgreSQL,",
                1,
            )
            with open(mod_md, "w", encoding="utf-8") as f:
                f.write(custom_text)
            res = gen_v2.build_manuscript(
                template_path=self.TEMPLATE_DOCX,
                source_md_path=mod_md,
                output_docx_path=mod_docx,
                figures_dir=self.FIGURES_DIR,
                output_pdf_path=None,
            )
            self.assertIn("DYNAMIC_ABSTRACT_SENTINEL_CHECK", res["abstract"])
            self.assertIn("DYNAMIC_KEYWORD_SENTINEL", res["keywords"])

    def test_08_ooxml_validation_and_footer_removal(self):
        """Gate 10 & 11: Validate OOXML Transitional conformance, 15 sectPr elements, relationships, and footer removal."""
        with zipfile.ZipFile(self.OUT_DOCX, "r") as z:
            self.assertIsNone(z.testzip())
            names = set(z.namelist())
            self.assertNotIn("word/footer1.xml", names)

            for name in names:
                if name.endswith((".xml", ".rels")):
                    raw = z.read(name)
                    self.assertNotIn(b"http://purl.oclc.org/ooxml/", raw, f"Strict NS URI left in {name}")
                    root = ET.fromstring(raw)
                    for el in root.iter():
                        for ak, av in el.attrib.items():
                            self.assertIsNone(
                                gen_v2.PT_RE.match(av),
                                f"Unnormalized pt-suffixed attribute in {name}: {el.tag} {ak}={av}",
                            )

            doc_root = ET.fromstring(z.read("word/document.xml"))
            self.assertIsNone(doc_root.get(f"{{{gen_v2.W_NS}}}conformance"))
            self.assertEqual(len(doc_root.xpath("//*[local-name()='footerReference']")), 0)
            self.assertEqual(len(doc_root.xpath("//*[local-name()='titlePg']")), 0)

            # Verify exact section property counts: 15 total (14 paragraph-level w:pPr/w:sectPr + 1 body-level w:body/w:sectPr)
            all_sect_pr = doc_root.xpath("//*[local-name()='sectPr']")
            p_sect_pr = doc_root.xpath("//*[local-name()='pPr']/*[local-name()='sectPr']")
            body_sect_pr = doc_root.xpath("//*[local-name()='body']/*[local-name()='sectPr']")
            self.assertEqual(len(all_sect_pr), 15, "Expected 15 total w:sectPr elements in word/document.xml")
            self.assertEqual(len(p_sect_pr), 14, "Expected 14 paragraph-level w:pPr/w:sectPr elements")
            self.assertEqual(len(body_sect_pr), 1, "Expected 1 final body-level w:body/w:sectPr element")

            # Check numbering.xml still has all 85 <w:lvl><w:start> elements across the 21 abstractNum definitions intact
            num_root = ET.fromstring(z.read("word/numbering.xml"))
            lvl_starts = num_root.xpath("//*[local-name()='lvl']/*[local-name()='start']")
            self.assertEqual(len(lvl_starts), 85)

            # Verify all relationships in word/_rels/document.xml.rels resolve to existing archive targets
            rels_root = ET.fromstring(z.read("word/_rels/document.xml.rels"))
            for rel in rels_root:
                rtype = rel.get("Type", "")
                rtarget = rel.get("Target", "")
                tmode = rel.get("TargetMode", "")
                self.assertFalse(rtype.endswith("/footer"), f"Footer relationship left: {rtarget}")
                self.assertNotEqual(tmode, "External", f"Dangling external relationship left: {rtarget}")
                norm_target = os.path.normpath(os.path.join("word", rtarget))
                self.assertIn(norm_target, names, f"Missing internal relationship target: {norm_target}")

            # Verify [Content_Types].xml has no override for /word/footer1.xml
            ct_root = ET.fromstring(z.read("[Content_Types].xml"))
            for ov in ct_root:
                if ov.get("PartName"):
                    p_name = ov.get("PartName").lstrip("/")
                    self.assertIn(p_name, names, f"Content_Types Override points to missing part: {p_name}")

        self.assertNotIn("XXX-X-XXXX", self.pdf_text)
        self.assertNotIn("©20XX IEEE", self.pdf_text)

    def test_09_metadata_and_placeholders(self):
        """Gate 14: Verify DOCX core/app metadata, PDF metadata, and honest author/funding/AI/repository placeholders."""
        with zipfile.ZipFile(self.OUT_DOCX, "r") as z:
            core_root = ET.fromstring(z.read("docProps/core.xml"))
            app_root = ET.fromstring(z.read("docProps/app.xml"))

        title_el = core_root.find(f"{{{gen_v2.DC_NS}}}title")
        creator_el = core_root.find(f"{{{gen_v2.DC_NS}}}creator")
        mod_by_el = core_root.find(f"{{{gen_v2.CP_NS}}}lastModifiedBy")
        created_el = core_root.find(f"{{{gen_v2.DCTERMS_NS}}}created")

        expected_title = "How FP16 Vector Representation and TOAST Storage Layouts Shift Query Plan Selection in PostgreSQL: An Empirical and Cost-Model Study"
        self.assertEqual(title_el.text, expected_title)
        self.assertEqual(creator_el.text, "Yash Pradhan")
        self.assertEqual(mod_by_el.text, "Yash Pradhan")
        self.assertNotEqual(created_el.text, "2024-07-16T13:42:00Z")

        words_val = int(app_root.find(f"{{{gen_v2.EXT_NS}}}Words").text)
        chars_val = int(app_root.find(f"{{{gen_v2.EXT_NS}}}Characters").text)
        chars_sp_val = int(app_root.find(f"{{{gen_v2.EXT_NS}}}CharactersWithSpaces").text)
        pages_val = int(app_root.find(f"{{{gen_v2.EXT_NS}}}Pages").text)
        self.assertGreater(words_val, 10000)
        self.assertLess(chars_val, chars_sp_val, "Characters (no spaces) must be < CharactersWithSpaces")
        self.assertEqual(pages_val, len(self.pdf_reader.pages))

        # Check PDF metadata
        self.assertEqual(self.pdf_reader.metadata.get("/Title"), expected_title)

        # Check unconfirmed author, funding, AI disclosure, and repository placeholders are preserved
        full_doc_text = "\n".join(p.text for p in self.doc.paragraphs)
        for req_ph in [
            "[Department / School Affiliation — Author Confirmation Required]",
            "[Institution / University / Independent Affiliation — Author Confirmation Required]",
            "[City, State/Province, Country — Author Confirmation Required]",
            "Email: [Author Email — Confirmation Required] | ORCID: [Author ORCID — Confirmation Required]",
            "[Author Confirmation Required — Funding Statement:",
            "AI-Use Disclosure (Provisional — Subject to Author Confirmation",
            "[Supplementary Material — Repository/DOI Placeholder]",
        ]:
            self.assertIn(req_ph, full_doc_text, f"Required placeholder missing from DOCX: {req_ph}")

        # Verify exact count of [Supplementary Material — Repository/DOI Placeholder]: 31 in source MD vs 28 in DOCX
        ph_token = "[Supplementary Material — Repository/DOI Placeholder]"
        self.assertEqual(self.md_text.count(ph_token), 31)
        p_ph_count = sum(p.text.count(ph_token) for p in self.doc.paragraphs)
        t_ph_count = sum(c.text.count(ph_token) for tbl in self.doc.tables for row in tbl.rows for c in row.cells)
        self.assertEqual(p_ph_count, 28, "Expected 28 occurrences of repository placeholder in DOCX paragraphs")
        self.assertEqual(t_ph_count, 0, "Expected 0 occurrences of repository placeholder in DOCX table cells")

    def test_10_source_to_output_content_preservation(self):
        """Gate 12: Complete 1-to-1 paragraph-by-paragraph (187 paragraphs) and cell-by-cell (980 cells) comparison."""
        non_empty_paras = [p for p in self.doc.paragraphs if p.text.strip()]
        self.assertEqual(len(non_empty_paras), 187, f"Expected 187 non-empty paragraphs, found {len(non_empty_paras)}")

        tmp_doc = docx.Document()

        def render_md_inline(raw_s: str, is_eq: bool = False) -> str:
            p = tmp_doc.add_paragraph()
            if is_eq:
                gen_v2.add_math_runs(p, raw_s)
            else:
                gen_v2.add_formatted_runs(p, raw_s)
            return p.text.strip()

        # 1. Reconstruct all expected paragraphs and tables directly from final_research_paper_source_v1.3.2.md
        exp_paras = []
        md_tables = []
        exp_paras.append(("paper title", render_md_inline(self.md_lines[0].lstrip("# ").strip())))
        exp_paras.append(("Author", render_md_inline(self.md_lines[2].replace("**", "").strip())))
        for aff in [self.md_lines[3].strip(), self.md_lines[4].strip(), self.md_lines[5].strip(), self.md_lines[6].strip()]:
            exp_paras.append(("Affiliation", render_md_inline(aff)))

        i = 7
        n_lines = len(self.md_lines)
        in_references = False
        in_code_block = False
        code_lines = []
        while i < n_lines:
            raw_line = self.md_lines[i]
            line = raw_line.strip()
            if not line:
                i += 1
                continue
            if line.startswith("```"):
                if not in_code_block:
                    in_code_block = True
                    code_lines = []
                else:
                    in_code_block = False
                    for cl in code_lines:
                        exp_paras.append(("Body Text", cl.strip()))
                i += 1
                continue
            if in_code_block:
                code_lines.append(raw_line)
                i += 1
                continue
            if line == "## Abstract" or re.match(r"^-{3,}$", line):
                i += 1
                continue
            if line.startswith("|"):
                t_lines = []
                while i < n_lines and self.md_lines[i].strip().startswith("|"):
                    t_lines.append(self.md_lines[i].strip())
                    i += 1
                rows = []
                for tl in t_lines:
                    cells = gen_v2.split_md_row(tl)
                    if all(re.match(r"^[:\-\s]+$", c) for c in cells if c):
                        continue
                    rows.append(cells)
                md_tables.append(rows)
                continue
            if line.startswith("**Abstract**—"):
                body_abs = line[len("**Abstract**—"):].strip()
                exp_paras.append(("Abstract", f"Abstract—{render_md_inline(body_abs)}"))
                i += 1
                continue
            if line.startswith("*Keywords*—"):
                body_kw = line[len("*Keywords*—"):].strip()
                exp_paras.append(("Keywords", f"Keywords—{render_md_inline(body_kw)}"))
                i += 1
                continue
            if line.startswith("## "):
                raw_h = line[3:].strip()
                if raw_h.startswith("Appendix ") or raw_h.startswith("Acknowledgment") or raw_h.startswith("References"):
                    exp_paras.append(("Heading 5", render_md_inline(raw_h)))
                    in_references = raw_h.startswith("References")
                else:
                    clean_h = re.sub(r"^[IVXLCDM]+\.\s+", "", raw_h)
                    exp_paras.append(("Heading 1", render_md_inline(clean_h)))
                    in_references = False
                i += 1
                continue
            if line.startswith("### "):
                raw_h2 = line[4:].strip()
                clean_h2 = re.sub(r"^[A-Z]\.\s+", "", raw_h2)
                exp_paras.append(("Heading 2", render_md_inline(clean_h2)))
                i += 1
                continue
            if line.startswith("#### "):
                st_text = line[5:].strip()
                exp_paras.append(("table head", render_md_inline(st_text)))
                i += 1
                continue
            if in_references and re.match(r"^\[\d+\]\s+", line):
                ref_body = re.sub(r"^\[\d+\]\s+", "", line)
                exp_paras.append(("references", render_md_inline(ref_body)))
                i += 1
                continue
            if line.startswith("$$"):
                eq_lines = []
                if line != "$$" and line.endswith("$$") and len(line) > 4:
                    eq_lines.append(line[2:-2].strip())
                    i += 1
                else:
                    if line != "$$":
                        eq_lines.append(line[2:].strip())
                    i += 1
                    while i < n_lines:
                        cur = self.md_lines[i].strip()
                        if cur.endswith("$$"):
                            if cur != "$$":
                                eq_lines.append(cur[:-2].strip())
                            i += 1
                            break
                        eq_lines.append(cur)
                        i += 1
                eq_raw = " ".join(eq_lines).strip()
                m_tag = re.search(r"\\tag\{([^}]+)\}\s*$", eq_raw)
                if m_tag:
                    eq_num = m_tag.group(1).strip()
                    eq_body = eq_raw[:m_tag.start()].strip()
                    exp_paras.append(("equation", f"{render_md_inline(eq_body, is_eq=True)}\t({eq_num})"))
                else:
                    exp_paras.append(("equation", render_md_inline(eq_raw, is_eq=True)))
                continue
            if line.startswith(">") and ("[FIGURE" in line or "Fig." in line):
                fig_lines = []
                while i < n_lines and self.md_lines[i].strip().startswith(">"):
                    fig_lines.append(self.md_lines[i].strip()[1:].strip())
                    i += 1
                cap_lines = [l for l in fig_lines if not (l.startswith("**[FIGURE") or l.startswith("[FIGURE"))]
                cap_raw = " ".join(cap_lines).strip()
                cap_body = re.sub(r"^\*\*Fig\.\s*\d+\.\*\*\s*", "", cap_raw).strip()
                if cap_body.startswith("*") and cap_body.endswith("*") and not cap_body.startswith("**"):
                    cap_body = cap_body[1:-1].strip()
                exp_paras.append(("figure caption", render_md_inline(cap_body)))
                continue
            if re.match(r"^\*\*TABLE\s+[IVXLCDM0-9A-Z-]+\*\*$", line):
                tbl_label = line.strip("*").strip()
                i += 1
                tbl_title = ""
                while i < n_lines and not self.md_lines[i].strip():
                    i += 1
                if i < n_lines and self.md_lines[i].strip().startswith("**") and not self.md_lines[i].strip().startswith("**TABLE"):
                    t_line = self.md_lines[i].strip()
                    if t_line.startswith("**") and t_line.endswith("**"):
                        tbl_title = t_line[2:-2].strip()
                    else:
                        tbl_title = t_line
                    i += 1
                exp_paras.append(("table head", render_md_inline(f"{tbl_label}. {tbl_title}" if tbl_title else tbl_label)))
                continue
            if line.startswith("*\\*") or line.startswith("*Note:") or line.startswith("**Note:"):
                fn_raw = line
                if fn_raw.startswith("*") and fn_raw.endswith("*") and not fn_raw.startswith("**"):
                    fn_body = fn_raw[1:-1].strip()
                else:
                    fn_body = fn_raw
                exp_paras.append(("table footnote", render_md_inline(fn_body)))
                i += 1
                continue
            m_bul = re.match(r"^(\s*)-\s+(.*)$", raw_line)
            if m_bul:
                exp_paras.append(("bullet list", render_md_inline(m_bul.group(2).strip())))
                i += 1
                continue
            exp_paras.append(("Body Text", render_md_inline(line)))
            i += 1

        # Verify all 187 non-empty paragraphs match 1-to-1 in order, style, and rendered text
        self.assertEqual(len(exp_paras), 187)
        for idx, ((exp_style, exp_txt), actual_p) in enumerate(zip(exp_paras, non_empty_paras)):
            self.assertEqual(actual_p.style.name, exp_style, f"P[{idx}] style {actual_p.style.name!r} != {exp_style!r}")
            self.assertEqual(actual_p.text.strip(), exp_txt, f"P[{idx}] text mismatch")

        # 2. Verify all 9 tables and all 980 table cells match 1-to-1 against source Markdown
        self.assertEqual(len(md_tables), 9)
        self.assertEqual(len(self.doc.tables), 9)
        compared_cells = 0
        for t_idx, (md_rows, d_tbl) in enumerate(zip(md_tables, self.doc.tables)):
            self.assertEqual(len(md_rows), len(d_tbl.rows), f"Table {t_idx} row count mismatch")
            for r_idx, (md_row, d_row) in enumerate(zip(md_rows, d_tbl.rows)):
                non_empty_md = [c for c in md_row if c]
                if len(non_empty_md) == 1 and len(md_row) >= 1:
                    exp_txt = render_md_inline(non_empty_md[0])
                    actual_txt = d_row.cells[0].text.strip()
                    self.assertEqual(actual_txt, exp_txt, f"Table {t_idx} R{r_idx} group header mismatch")
                    compared_cells += len(d_row.cells)
                else:
                    self.assertEqual(len(md_row), len(d_row.cells), f"Table {t_idx} R{r_idx} column count mismatch")
                    for c_idx, (md_cell, d_cell) in enumerate(zip(md_row, d_row.cells)):
                        exp_txt = render_md_inline(md_cell)
                        actual_txt = d_cell.text.strip()
                        self.assertEqual(actual_txt, exp_txt, f"Table {t_idx} R{r_idx}C{c_idx} cell text mismatch")
                        compared_cells += 1
        self.assertEqual(compared_cells, 980, f"Expected 980 compared table cells, got {compared_cells}")

        # 3. Verify all 25 references and exact hardware specification
        ref_paras = [p.text for p in self.doc.paragraphs if p.style.name == "references"]
        self.assertEqual(len(ref_paras), 25)
        self.assertTrue(ref_paras[0].startswith("P. Lewis, E. Perez, A. Piktus"))
        self.assertIn("2026 IEEE 42nd Int. Conf. Data Eng. (ICDE 2026)", ref_paras[9])
        self.assertTrue(ref_paras[24].startswith("IEEE Standard for Floating-Point Arithmetic"))

        full_doc_text = "\n".join(p.text for p in self.doc.paragraphs)
        self.assertIn("Intel Core Ultra 9 185H CPU (16 physical cores, 22 logical processors), 32 GB RAM", full_doc_text)
        self.assertNotIn("Ryzen 7 5800H", full_doc_text)

    def test_11_nested_lists_and_missing_figure_fallback(self):
        """Gate 15: Verify 2-level nested bullet lists and safe missing-figure fallback behavior."""
        bullet_paras = [p for p in self.doc.paragraphs if p.style.name == "bullet list"]
        self.assertEqual(len(bullet_paras), 12, f"Expected 12 bullet paragraphs (3 top-level + 9 nested), found {len(bullet_paras)}")
        ilvls = []
        for bp in bullet_paras:
            ilvl_els = bp._p.xpath("./*[local-name()='pPr']/*[local-name()='numPr']/*[local-name()='ilvl']")
            ilvls.append(int(ilvl_els[0].get(f"{{{gen_v2.W_NS}}}val")) if ilvl_els else 0)
        self.assertEqual(ilvls.count(0), 3, "Expected 3 top-level bullets (RQ1..RQ3)")
        self.assertEqual(ilvls.count(1), 9, "Expected 9 nested level-1 sub-bullets")

        # Missing-figure fallback test
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_figs = os.path.join(tmpdir, "empty_figs")
            os.makedirs(empty_figs, exist_ok=True)
            fallback_docx = os.path.join(tmpdir, "fallback.docx")
            res = gen_v2.build_manuscript(
                template_path=self.TEMPLATE_DOCX,
                source_md_path=self.SOURCE_MD,
                output_docx_path=fallback_docx,
                figures_dir=empty_figs,
                output_pdf_path=None,
            )
            self.assertEqual(len(res["missing_figures"]), 3)
            d_fb = docx.Document(fallback_docx)
            fb_text = "\n".join(p.text for p in d_fb.paragraphs)
            for fno in (1, 2, 3):
                self.assertIn(f"[MISSING SOURCE FIGURE ASSET: figure_0{fno}.png", fb_text)

    def test_12_package_and_pdf_integrity(self):
        """Gate 4, 13, 16: Verify DOCX/PDF structural integrity, LibreOffice 7.4.7.2 page count, Figure 2 caption co-location, and text parity."""
        self.assertTrue(os.path.isfile(self.OUT_DOCX))
        self.assertTrue(os.path.isfile(self.OUT_PDF))
        self.assertGreater(os.path.getsize(self.OUT_DOCX), 3_000_000)
        self.assertGreater(os.path.getsize(self.OUT_PDF), 2_000_000)
        pdf_doc = pdfium.PdfDocument(self.OUT_PDF)
        self.assertEqual(len(pdf_doc), 21)
        self.assertEqual(len(self.pdf_reader.pages), 21)

        # Verify Page 12 contains the entire Figure 2 caption without spilling onto Page 13
        page_12_text = self.pdf_reader.pages[11].extract_text()
        page_13_text = self.pdf_reader.pages[12].extract_text()
        self.assertIn("Fig. 2. Unforced Planner Transition Map", page_12_text)
        self.assertIn("Wilcoxon signed-rank p-values across the 9-test family", page_12_text)
        self.assertNotIn("Fig. 2. Unforced Planner Transition Map", page_13_text)
        self.assertNotIn("Wilcoxon signed-rank p-values across the 9-test family", page_13_text)
        self.assertIn("TABLE III. NON-PARAMETRIC STATISTICAL INFERENCE SUMMARY", page_13_text)

        # Verify DOCX-to-PDF extracted-text parity across all major headings, tables, figures, and references
        pdf_norm = re.sub(r"-\s+", "-", re.sub(r"\s+", " ", self.pdf_text))
        for key_token in [
            "How FP16 Vector Representation and TOAST Storage Layouts Shift Query Plan Selection in PostgreSQL",
            "I. INTRODUCTION",
            "II. BACKGROUND AND SOURCE-LEVEL COST-MODEL ANALYSIS",
            "TABLE I. THREE-LEVEL NUMERICAL COST RECONSTRUCTION",
            "Fig. 1. PostgreSQL 18.4 and pgvector 0.8.4 Storage-Layout and Cost-Propagation Pipeline",
            "III. RELATED WORK",
            "IV. EXPERIMENTAL METHODOLOGY",
            "V. EMPIRICAL RESULTS",
            "TABLE II. PHYSICAL STORAGE FOOTPRINT",
            "TABLE II-B. 18-SCALE SWEEP",
            "TABLE II-C. OBSERVED PLANNER CROSSOVER INTERVALS",
            "Fig. 2. Unforced Planner Transition Map",
            "TABLE III. NON-PARAMETRIC STATISTICAL INFERENCE SUMMARY",
            "TABLE V. ANALYTICAL DIMENSIONALITY REGIMES",
            "VI. DISCUSSION, DIMENSIONALITY REGIMES, PRACTICAL GUIDELINES, AND LIMITATIONS",
            "VII. CONCLUSION",
            "APPENDIX A: SECONDARY ANALYSIS",
            "TABLE IV. QUERY-LEVEL RETRIEVAL DECOMPOSITION",
            "Fig. 3. Query-Level Retrieval Decomposition",
            "ACKNOWLEDGMENT",
            "REFERENCES",
            "[25] IEEE Standard for Floating-Point Arithmetic, IEEE Std 754-2019",
        ]:
            self.assertIn(key_token, pdf_norm, f"Expected structural text token missing from rendered PDF: {key_token}")

    def test_13_v133_scientific_revisions_and_no_v132_regression(self):
        """Phase 5C Gate: Verify all 4 V1.3.3 scientific corrections are present in DOCX & PDF and zero V1.3.2 superseded phrases remain."""
        full_doc_text = "\n".join(p.text for p in self.doc.paragraphs)
        pdf_norm = re.sub(r"-\s+", "-", re.sub(r"\s+", " ", self.pdf_text))

        # 1. All 4 approved V1.3.3 scientific text revisions must be present verbatim
        v133_required = [
            "Passages and queries are represented as 768-dimensional embeddings using the mutable Ollama model tag nomic-embed-text:latest [16]. The exact model artifact digest and Ollama runtime build were not recorded; consequently, the original embedding-generation environment cannot be reconstructed exactly from the available provenance.",
            "Latency measurements characterize the observed benchmark runs; consistency of latency distributions across independent reruns was not established;",
            "Each table uses one HNSW build (m = 16, efconstruction = 64); because repeated graph builds were not evaluated, the contribution of graph-construction variability to the observed 0.005 recall differences under forced_hnsw cannot be isolated, and inferences are conditioned on the 20 fixed queries (q0–q19);",
            "enabling offline reproduction of the post-collection cost-model calculations, statistical tests, bootstrap confidence intervals, tables, and figures from the preserved evidence. This does not establish complete from-scratch reproduction of corpus construction, embedding generation, or the original database state.",
        ]
        for req_s in v133_required:
            self.assertIn(req_s, full_doc_text, f"Missing V1.3.3 required text in DOCX: {req_s[:80]}")

        for pdf_s in [
            "represented as 768-dimensional embeddings using the mutable Ollama model tag nomic-embed-text:latest [16]. The exact model artifact digest and Ollama runtime build were not recorded",
            "Latency measurements characterize the observed benchmark runs; consistency of latency distributions across independent reruns was not established",
            "because repeated graph builds were not evaluated, the contribution of graph-construction variability to the observed 0.005 recall differences under forced_hnsw cannot be isolated",
            "enabling offline reproduction of the post-collection cost-model calculations, statistical tests, bootstrap confidence intervals, tables, and figures from the preserved evidence. This does not establish complete from-scratch reproduction of corpus construction, embedding generation, or the original database state.",
        ]:
            self.assertIn(pdf_s, pdf_norm, f"Missing V1.3.3 required text in PDF: {pdf_s[:80]}")

        # 2. Superseded V1.3.2 wording must NOT appear in DOCX or PDF
        v132_forbidden = [
            "Passages and queries are embedded into 768 dimensions using nomic-embed-text:latest [16] via local Ollama.",
            "so 0.005 recall differences under forced_hnsw lie within single-graph construction variance",
            "enabling 100% offline reproduction of all cost-model calculations",
        ]
        for bad_s in v132_forbidden:
            self.assertNotIn(bad_s, full_doc_text, f"Superseded V1.3.2 wording found in DOCX: {bad_s}")
            self.assertNotIn(bad_s, pdf_norm, f"Superseded V1.3.2 wording found in PDF: {bad_s}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
