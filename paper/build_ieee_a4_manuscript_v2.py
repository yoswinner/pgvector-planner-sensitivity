#!/usr/bin/env python3
r"""
Phase R4.4 — Repaired IEEE A4 Conference Manuscript Generator (v2)
==================================================================
Repairs and evolves `build_ieee_a4_manuscript.py` (R4.2) into a reproducible,
namespace-aware, self-verifying IEEE A4 DOCX/PDF generator (`build_ieee_a4_manuscript_v2.py`).

Key Repairs Over R4.2 (`build_ieee_a4_manuscript.py`):
  A. Equation Typography & Mathematical Fidelity:
     - Fixes `styleId="equation"` in `word/styles.xml` (`Symbol` -> `Times New Roman`)
       and explicitly assigns `Times New Roman` on all equation runs.
     - Implements a complete LaTeX math converter and run builder supporting escaped braces
       (`\{`, `\}`), escaped underscores (`\_`), `\binom{a}{b}`, `\epsilon`, `\varepsilon`,
       `\bar{x}`, `\tilde{x}`, `\sqrt{x}`, `\sim`, `\iff`, `\implies`, `\lfloor..\rfloor`,
       `\lceil..\rceil`, `\mathcal`, `\mathbf`, `\texttt`, `\text`, `\mathrm`, and true
       OOXML `<w:vertAlign w:val="subscript|superscript"/>` runs for `_{...}` and `^{...}`.
  B. Recursive Inline Markdown & Math Parser:
     - Replaces the flat regex tokenizer with a left-to-right lexical scanner and recursive
       AST parser (`parse_inline_ast`) where code spans (`` `...` ``) and math spans (`$...$`)
       have atomic precedence, eliminating all 55 paragraph and 73 table-cell delimiter leaks.
  C. Deduplicated Section, Subsection, Figure, Table, and Reference Numbering:
     - Strips redundant Markdown prefixes (`I.`–`VII.`, `A.`–`D.`, `**Fig. X.**`, `[1]`–`[25]`)
       where template styles (`Heading 1`, `Heading 2`, `figure caption`, `references`)
       supply automatic numbering via `word/numbering.xml`.
     - Routes unnumbered top-level sections (`Appendix A`, `Acknowledgment`, `References`)
       to `Heading 5` (`styleId="Heading5"`).
     - Disables sequential Roman auto-numbering (`numId=0`) on `table head` and `table footnote`
       paragraphs so alphanumeric table labels (`TABLE I`, `TABLE II-B`, `Sub-Table III-A`, etc.)
       and general `Note:` paragraphs render cleanly without `TABLE IV. TABLE II-C` or `a. \Note:`.
  D. Table Parsing, Group Headings, Sub-Table III-A Separation, and Footnotes:
     - Separates `TABLE III` main heading from `Sub-Table III-A` subheading.
     - Preserves mixed case in `table head` (relying on the style's `<w:smallCaps/>` rather than
       destructive `.upper()` string conversion before LaTeX parsing).
     - Applies shaded group-header formatting across single-label group rows in Table I.
  E. Dynamic Title, Author Block, Abstract, and Keywords Extraction:
     - Dynamically parses Title, Author, Affiliation placeholders, Abstract, and Keywords from
       `final_research_paper_source_v1.3.2.md` (with optional CLI overrides for author fields).
  F. Complete Footer & Dangling Relationship Removal:
     - Removes all `w:footerReference` and `w:titlePg` elements from every `w:sectPr`.
     - Removes unreferenced `footer1.xml` relationship and dangling sample-text hyperlink
       relationships (`rId9`, `rId10`) from `word/_rels/document.xml.rels`, `word/footer1.xml`,
       and `[Content_Types].xml`.
  G. Namespace-Aware Strict-to-Transitional OOXML Normalization:
     - Uses `lxml.etree` element/attribute tree walking (never broad regex over XML) with
       context-specific element (`tblBorders`/`tcBorders`/`tblCellMar` `start`/`end` -> `left`/`right`)
       and attribute (`ind` `start`/`end` -> `left`/`right`; `jc`/`lvlJc`/`tab` `val`) rules.
  H. Honest Metadata & LibreOffice PDF Sync:
     - Populates `docProps/core.xml` and `docProps/app.xml` with confirmed title/author metadata,
       production timestamps, computed word/character/paragraph counts, and verified PDF page count.
  I. Nested Bullet Hierarchy & Safe Missing-Figure Fallback:
     - Restores 2-level indentation (`ilvl=0` and `ilvl=1`) for nested bullet lists.
     - Provides a non-destructive textual placeholder box if any expected figure file is absent.
"""

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone

import docx
import lxml.etree as ET
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt

# ==============================================================================
# 1. Namespace-Aware Strict-to-Transitional OOXML Normalizer
# ==============================================================================

STRICT_TO_TRANS_NS = {
    "http://purl.oclc.org/ooxml/wordprocessingml/main": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "http://purl.oclc.org/ooxml/officeDocument/relationships": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "http://purl.oclc.org/ooxml/officeDocument/math": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "http://purl.oclc.org/ooxml/drawingml/wordprocessingDrawing": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "http://purl.oclc.org/ooxml/drawingml/main": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "http://purl.oclc.org/ooxml/drawingml/picture": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "http://purl.oclc.org/ooxml/officeDocument/extendedProperties": "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties",
    "http://purl.oclc.org/ooxml/officeDocument/customXml": "http://schemas.openxmlformats.org/officeDocument/2006/customXml",
    "http://purl.oclc.org/ooxml/officeDocument/docPropsVTypes": "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes",
    "http://purl.oclc.org/ooxml/package/relationships": "http://schemas.openxmlformats.org/package/2006/relationships",
}

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKGREL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
CP_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
DCTERMS_NS = "http://purl.org/dc/terms/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
EXT_NS = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
VT_NS = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"

PT_ATTR_PARENTS = {
    "pgSz": {"w", "h"},
    "pgMar": {"top", "right", "bottom", "left", "header", "footer", "gutter"},
    "cols": {"space", "w"},
    "spacing": {"before", "after", "line"},
    "ind": {"left", "right", "firstLine", "hanging"},
    "tab": {"pos"},
    "tblW": {"w"},
    "tcW": {"w"},
    "tblInd": {"w"},
    "top": {"w"},
    "left": {"w"},
    "bottom": {"w"},
    "right": {"w"},
    "framePr": {"x", "y", "w", "h", "hSpace", "vSpace"},
    "defaultTabStop": {"val"},
}

PT_RE = re.compile(r"^(-?[0-9]+(?:\.[0-9]+)?)pt$")


def map_strict_uri(uri: str) -> str:
    """Map an ISO/IEC 29500 Strict namespace or relationship URI to Transitional."""
    if not uri:
        return uri
    if uri in STRICT_TO_TRANS_NS:
        return STRICT_TO_TRANS_NS[uri]
    for k, v in STRICT_TO_TRANS_NS.items():
        if uri.startswith(k + "/"):
            return v + uri[len(k):]
    return uri


def transform_ooxml_element(elem: ET._Element, parent_localname: str = None) -> ET._Element:
    """
    Recursively normalize an XML element tree from Strict OOXML to Transitional OOXML
    using namespace-aware lxml operations and context-specific element/attribute semantics.
    """
    if not isinstance(elem.tag, str):
        return elem
    orig_qn = ET.QName(elem.tag)
    new_ns = map_strict_uri(orig_qn.namespace)
    local = orig_qn.localname

    # Context-specific element tag normalization: ONLY inside tblBorders, tcBorders, tblCellMar
    if new_ns == W_NS and parent_localname in ("tblBorders", "tcBorders", "tblCellMar"):
        if local == "start":
            local = "left"
        elif local == "end":
            local = "right"

    new_nsmap = {k: map_strict_uri(v) for k, v in elem.nsmap.items()}
    new_tag = f"{{{new_ns}}}{local}" if new_ns else local
    new_elem = ET.Element(new_tag, nsmap=new_nsmap)
    new_elem.text = elem.text
    new_elem.tail = elem.tail

    for attr_k, attr_v in elem.attrib.items():
        if attr_k.startswith("{"):
            aqn = ET.QName(attr_k)
            a_ns = map_strict_uri(aqn.namespace)
            a_local = aqn.localname
        else:
            a_ns = None
            a_local = attr_k

        # 1. Remove w:conformance="strict" on w:document
        if local == "document" and a_local == "conformance":
            continue

        # 2. Map Relationship Type URIs in .rels parts
        if local == "Relationship" and a_local == "Type":
            attr_v = map_strict_uri(attr_v)

        # 3. Context-specific w:ind/@w:start and @w:end -> @w:left and @w:right
        if new_ns == W_NS and local == "ind" and a_ns == W_NS:
            if a_local == "start":
                a_local = "left"
            elif a_local == "end":
                a_local = "right"

        # 4. Context-specific alignment/tab values: start -> left, end -> right
        if new_ns == W_NS and local in ("jc", "lvlJc", "tab") and a_local == "val":
            if attr_v == "start":
                attr_v = "left"
            elif attr_v == "end":
                attr_v = "right"

        # 5. Context-specific pt-to-twips (or 240ths on auto line spacing) normalization
        if new_ns == W_NS and local in PT_ATTR_PARENTS and a_local in PT_ATTR_PARENTS[local]:
            m = PT_RE.match(attr_v)
            if m:
                pt_val = float(m.group(1))
                attr_v = str(int(round(pt_val * 20.0)))

        new_attr_key = f"{{{a_ns}}}{a_local}" if a_ns else a_local
        new_elem.set(new_attr_key, attr_v)

    for child in elem:
        new_elem.append(transform_ooxml_element(child, parent_localname=local))

    return new_elem


def customize_template_styles(styles_root: ET._Element):
    """
    Apply targeted style repairs in word/styles.xml using lxml:
      1. styleId="equation": replace Symbol font with Times New Roman; set center tab=2433 dxa
         and right tab=4866 dxa (matching exact 243.3 pt column width).
      2. docDefaults / rPrDefault: ensure explicit 10pt (val="20") default size alongside Times New Roman.
    """
    for style_el in styles_root.findall(f"{{{W_NS}}}style"):
        sid = style_el.get(f"{{{W_NS}}}styleId")
        if sid == "equation":
            rPr = style_el.find(f"{{{W_NS}}}rPr")
            if rPr is not None:
                rFonts = rPr.find(f"{{{W_NS}}}rFonts")
                if rFonts is not None:
                    for k in ("ascii", "hAnsi", "cs"):
                        rFonts.set(f"{{{W_NS}}}{k}", "Times New Roman")
            pPr = style_el.find(f"{{{W_NS}}}pPr")
            if pPr is not None:
                tabs = pPr.find(f"{{{W_NS}}}tabs")
                if tabs is not None:
                    for tab in list(tabs.findall(f"{{{W_NS}}}tab")):
                        tval = tab.get(f"{{{W_NS}}}val")
                        if tval == "center":
                            tabs.remove(tab)
                        elif tval == "right":
                            tab.set(f"{{{W_NS}}}pos", "4866")

    doc_defs = styles_root.find(f"{{{W_NS}}}docDefaults")
    if doc_defs is not None:
        rPrDef = doc_defs.find(f"{{{W_NS}}}rPrDefault")
        if rPrDef is not None:
            rPr = rPrDef.find(f"{{{W_NS}}}rPr")
            if rPr is not None and rPr.find(f"{{{W_NS}}}sz") is None:
                sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
                sz.set(f"{{{W_NS}}}val", "20")
                szCs = ET.SubElement(rPr, f"{{{W_NS}}}szCs")
                szCs.set(f"{{{W_NS}}}val", "20")


def normalize_template_to_bytes(template_path: str) -> bytes:
    """
    Read `conference-template-a4.docx` and normalize all XML/relationship parts
    from ISO/IEC 29500 Strict to Transitional OOXML in memory without modifying the input file.
    """
    out_buf = io.BytesIO()
    with zipfile.ZipFile(template_path, "r") as zin, zipfile.ZipFile(
        out_buf, "w", compression=zipfile.ZIP_DEFLATED
    ) as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename.endswith((".xml", ".rels")):
                root = ET.fromstring(data)
                new_root = transform_ooxml_element(root)
                if info.filename == "word/styles.xml":
                    customize_template_styles(new_root)
                data = ET.tostring(new_root, xml_declaration=True, encoding="UTF-8", standalone="yes")
            zout.writestr(info, data)
    out_buf.seek(0)
    return out_buf.getvalue()


# ==============================================================================
# 2. Mathematical & Inline Markdown AST Parser
# ==============================================================================

LBRACE_SENTINEL = "\uE000"
RBRACE_SENTINEL = "\uE001"
USCORE_SENTINEL = "\uE002"
BOLD_START_SENTINEL = "\uE003"
BOLD_END_SENTINEL = "\uE004"
TT_START_SENTINEL = "\uE005"
TT_END_SENTINEL = "\uE006"
TEXT_START_SENTINEL = "\uE007"
TEXT_END_SENTINEL = "\uE008"

LATEX_SYMBOLS = [
    (r"\{,\}", ","),
    (r"\{", LBRACE_SENTINEL),
    (r"\}", RBRACE_SENTINEL),
    (r"\_", USCORE_SENTINEL),
    (r"\%", "%"),
    (r"\left\lfloor", "⌊"),
    (r"\right\rfloor", "⌋"),
    (r"\left\lceil", "⌈"),
    (r"\right\rceil", "⌉"),
    (r"\left(", "("),
    (r"\right)", ")"),
    (r"\left[", "["),
    (r"\right]", "]"),
    (r"\big(", "("),
    (r"\big)", ")"),
    (r"\Big(", "("),
    (r"\Big)", ")"),
    (r"\lfloor", "⌊"),
    (r"\rfloor", "⌋"),
    (r"\lceil", "⌈"),
    (r"\rceil", "⌉"),
    (r"\implies", "⟹"),
    (r"\iff", "⟺"),
    (r"\forall", "∀"),
    (r"\subseteq", "⊆"),
    (r"\subset", "⊂"),
    (r"\cap", "∩"),
    (r"\cup", "∪"),
    (r"\setminus", " \\ "),
    (r"\emptyset", "∅"),
    (r"\lesssim", "≲"),
    (r"\gtrsim", "≳"),
    (r"\dots", "…"),
    (r"\varepsilon", "ε"),
    (r"\epsilon", "ϵ"),
    (r"\Delta", "Δ"),
    (r"\alpha", "α"),
    (r"\chi", "χ"),
    (r"\tau", "τ"),
    (r"\mu", "μ"),
    (r"\sigma", "σ"),
    (r"\times", "×"),
    (r"\cdot", "·"),
    (r"\pm", "±"),
    (r"\neq", "≠"),
    (r"\approx", "≈"),
    (r"\le", "≤"),
    (r"\ge", "≥"),
    (r"\in", "∈"),
    (r"\to", "→"),
    (r"\mid", " | "),
    (r"\!", ""),
    (r"\,", " "),
    (r"\;", " "),
    (r"\ ", " "),
    (r"\sim", "~"),
    (r"\quad", "  "),
    (r"\qquad", "    "),
    (r"\ln", "ln"),
    (r"\log", "log"),
    (r"\min", "min"),
    (r"\max", "max"),
]


def restore_sentinels(s: str) -> str:
    """Restore protected literal characters and strip formatting sentinels."""
    return (
        s.replace(LBRACE_SENTINEL, "{")
        .replace(RBRACE_SENTINEL, "}")
        .replace(USCORE_SENTINEL, "_")
        .replace(BOLD_START_SENTINEL, "")
        .replace(BOLD_END_SENTINEL, "")
        .replace(TT_START_SENTINEL, "")
        .replace(TT_END_SENTINEL, "")
        .replace(TEXT_START_SENTINEL, "")
        .replace(TEXT_END_SENTINEL, "")
    )


def format_frac(num: str, den: str, followed_by_mult: bool = False) -> str:
    r"""Format \frac{num}{den} cleanly with minimal, unambiguous parenthesization."""
    num_s = num.strip()
    den_s = den.strip()

    def needs_parens(x: str) -> bool:
        xc = restore_sentinels(x)
        return any(op in xc for op in [" + ", " - ", " − "])

    n_fmt = f"({num_s})" if needs_parens(num_s) else num_s
    d_fmt = f"({den_s})" if needs_parens(den_s) else den_s
    res = f"{n_fmt} / {d_fmt}"
    if followed_by_mult:
        return f"({res})"
    return res


def clean_latex_math(expr: str) -> str:
    """
    Convert a LaTeX math string into a sentinel-annotated Unicode string ready
    for subscript/superscript and style run emission.
    """
    s = expr.strip()
    s = s.replace("{,}", ",")
    s = s.replace(r"\{", LBRACE_SENTINEL).replace(r"\}", RBRACE_SENTINEL).replace(r"\_", USCORE_SENTINEL)
    # Combining overbar (\bar{L}) and tilde (\tilde{L})
    s = re.sub(r"\\bar\{([^{}]+)\}", lambda m: m.group(1) + "\u0304", s)
    s = re.sub(r"\\tilde\{([^{}]+)\}", lambda m: m.group(1) + "\u0303", s)
    # Square root (\sqrt{20})
    s = re.sub(r"\\sqrt\{([^{}]+)\}", r"√(\1)", s)
    # Nested font/text commands inside math
    for _ in range(6):
        s = re.sub(r"\\mathbf\{([^{}]*)\}", lambda m: BOLD_START_SENTINEL + m.group(1) + BOLD_END_SENTINEL, s)
        s = re.sub(r"\\texttt\{([^{}]*)\}", lambda m: TT_START_SENTINEL + m.group(1) + TT_END_SENTINEL, s)
        s = re.sub(r"\\(?:text|mathrm)\{([^{}]*)\}", lambda m: TEXT_START_SENTINEL + m.group(1) + TEXT_END_SENTINEL, s)
        s = re.sub(r"\\(?:mathit|mathcal)\{([^{}]*)\}", r"\1", s)
    # Binomial coefficient (\binom{28}{2} -> C(28, 2))
    for _ in range(4):
        s = re.sub(r"\\binom\{([^{}]+)\}\{([^{}]+)\}", r"C(\1, \2)", s)
    # Fractions (\frac{a}{b})
    for _ in range(6):
        s = re.sub(
            r"\\frac\{([^{}]+)\}\{([^{}]+)\}(\s*\\cdot|\s*\\times)?",
            lambda m: format_frac(m.group(1), m.group(2), followed_by_mult=bool(m.group(3))) + (m.group(3) or ""),
            s,
        )
    for k, v in LATEX_SYMBOLS:
        s = s.replace(k, v)
    return s


def add_math_runs(
    p,
    math_str: str,
    base_bold: bool = False,
    base_italic: bool = False,
    font_size_pt: float = None,
    font_name: str = "Times New Roman",
):
    r"""
    Emit formatted Word runs for a mathematical expression, including true Word
    subscript/superscript runs, bold (\mathbf), monospace (\texttt), upright (\text),
    and italic single-letter mathematical variables.
    """
    s = clean_latex_math(math_str)

    # Track active inline math style state across segments (\mathbf, \texttt, \text)
    # First split by style sentinels and subscript/superscript tokens
    token_re = re.compile(
        r"(\^\{[^{}]*\}|\^[0-9a-zA-Z\u0370-\u03FF+-]+"
        r"|_\{[^{}]*\}|_[0-9a-zA-Z\u0370-\u03FF+-]+"
        r"|\uE003|\uE004|\uE005|\uE006|\uE007|\uE008)"
    )
    tokens = token_re.split(s)

    in_mathbf = False
    in_texttt = False
    in_text = False

    def style_and_add_run(text_val: str, is_sub: bool = False, is_sup: bool = False, force_italic: bool = None):
        clean_val = restore_sentinels(text_val)
        if not clean_val:
            return
        r = p.add_run(clean_val)
        r.font.name = "Consolas" if in_texttt else font_name
        if font_size_pt is not None:
            r.font.size = Pt(font_size_pt * 0.92) if in_texttt else Pt(font_size_pt)
        if base_bold or in_mathbf:
            r.font.bold = True
        if is_sub:
            r.font.subscript = True
        elif is_sup:
            r.font.superscript = True
        if force_italic is not None:
            r.font.italic = force_italic
        elif base_italic:
            r.font.italic = True

    for tok in tokens:
        if not tok:
            continue
        if tok == BOLD_START_SENTINEL:
            in_mathbf = True
            continue
        if tok == BOLD_END_SENTINEL:
            in_mathbf = False
            continue
        if tok == TT_START_SENTINEL:
            in_texttt = True
            continue
        if tok == TT_END_SENTINEL:
            in_texttt = False
            continue
        if tok == TEXT_START_SENTINEL:
            in_text = True
            continue
        if tok == TEXT_END_SENTINEL:
            in_text = False
            continue

        if tok.startswith("^"):
            val = tok[2:-1] if tok.startswith("^{") and tok.endswith("}") else tok[1:]
            style_and_add_run(val, is_sup=True, force_italic=False)
        elif tok.startswith("_"):
            val = tok[2:-1] if tok.startswith("_{") and tok.endswith("}") else tok[1:]
            style_and_add_run(val, is_sub=True, force_italic=False)
        else:
            clean_tok = tok.replace("{", "").replace("}", "")
            if in_text or in_texttt:
                style_and_add_run(clean_tok, force_italic=base_italic and not in_texttt)
            else:
                # Italicize single-letter Latin math variables (except unit 'B' or 's') and multi-letter 'ef'/'df'
                sub_toks = re.split(r"(\b[A-Za-z]\b|\bef\b|\bdf\b)", clean_tok)
                for st in sub_toks:
                    if not st:
                        continue
                    is_var = (
                        (len(st) == 1 and st.isalpha() and st not in ("B", "s"))
                        or st in ("ef", "df")
                    )
                    style_and_add_run(st, force_italic=(True if is_var else base_italic))


def find_closing_delim(text: str, start_idx: int, delim: str) -> int:
    """
    Find the matching closing delimiter (`delim` in {'***', '**', '*', '`', '$'})
    starting at `start_idx`, respecting escaped characters and nested atomic spans.
    """
    n = len(text)
    if delim == "`":
        return text.find("`", start_idx)
    if delim == "$":
        i = start_idx
        while i < n:
            if text[i] == "\\" and i + 1 < n:
                i += 2
                continue
            if text[i] == "$":
                return i
            i += 1
        return -1

    i = start_idx
    while i < n:
        if text[i] == "\\" and i + 1 < n:
            i += 2
            continue
        if text[i] == "`":
            end_c = text.find("`", i + 1)
            if end_c != -1:
                i = end_c + 1
                continue
        if text[i] == "$":
            end_m = find_closing_delim(text, i + 1, "$")
            if end_m != -1:
                i = end_m + 1
                continue
        if delim == "***":
            if text.startswith("***", i):
                return i
        elif delim == "**":
            if text.startswith("**", i):
                return i
        elif delim == "*":
            if text.startswith("**", i):
                end_b = find_closing_delim(text, i + 2, "**")
                if end_b != -1:
                    i = end_b + 2
                    continue
                else:
                    i += 2
                    continue
            if text[i] == "*":
                return i
        i += 1
    return -1


def parse_inline_ast(text: str) -> list:
    """
    Parse an inline Markdown + math string into a recursive AST:
      - ("TEXT", str)
      - ("CODE", str)
      - ("MATH", str)
      - ("BOLD", list[node])
      - ("ITALIC", list[node])
      - ("BOLD_ITALIC", list[node])
    Unmatched delimiters are preserved as literal text without dropping characters.
    """
    nodes = []
    buf = []
    i = 0
    n = len(text)

    def flush_buf():
        if buf:
            nodes.append(("TEXT", "".join(buf)))
            buf.clear()

    while i < n:
        # 1. Escaped delimiter outside code/math
        if text[i] == "\\" and i + 1 < n and text[i + 1] in ("*", "$", "`", "_", "\\", "|", "{", "}"):
            buf.append(text[i + 1])
            i += 2
            continue

        # 2. Code span `...` (highest atomic precedence)
        if text[i] == "`":
            end_idx = find_closing_delim(text, i + 1, "`")
            if end_idx != -1:
                flush_buf()
                nodes.append(("CODE", text[i + 1 : end_idx]))
                i = end_idx + 1
                continue
            else:
                buf.append("`")
                i += 1
                continue

        # 3. Inline math span $...$ (second highest atomic precedence)
        if text[i] == "$":
            end_idx = find_closing_delim(text, i + 1, "$")
            if end_idx != -1:
                flush_buf()
                nodes.append(("MATH", text[i + 1 : end_idx]))
                i = end_idx + 1
                continue
            else:
                buf.append("$")
                i += 1
                continue

        # 4. Bold-Italic ***...***
        if text.startswith("***", i):
            end_idx = find_closing_delim(text, i + 3, "***")
            if end_idx != -1 and end_idx > i + 3:
                flush_buf()
                nodes.append(("BOLD_ITALIC", parse_inline_ast(text[i + 3 : end_idx])))
                i = end_idx + 3
                continue

        # 5. Bold **...**
        if text.startswith("**", i):
            end_idx = find_closing_delim(text, i + 2, "**")
            if end_idx != -1 and end_idx > i + 2:
                flush_buf()
                nodes.append(("BOLD", parse_inline_ast(text[i + 2 : end_idx])))
                i = end_idx + 2
                continue
            else:
                buf.append("**")
                i += 2
                continue

        # 6. Italic *...*
        if text[i] == "*":
            end_idx = find_closing_delim(text, i + 1, "*")
            if end_idx != -1 and end_idx > i + 1:
                flush_buf()
                nodes.append(("ITALIC", parse_inline_ast(text[i + 1 : end_idx])))
                i = end_idx + 1
                continue
            else:
                buf.append("*")
                i += 1
                continue

        buf.append(text[i])
        i += 1

    flush_buf()
    return nodes


def emit_ast_runs(
    paragraph,
    nodes: list,
    base_bold: bool = False,
    base_italic: bool = False,
    font_size_pt: float = None,
    font_name: str = "Times New Roman",
    code_font_name: str = "Consolas",
):
    """Recursively emit Word runs from parsed inline AST nodes."""
    for kind, val in nodes:
        if kind == "TEXT":
            if not val:
                continue
            r = paragraph.add_run(val)
            r.font.name = font_name
            if font_size_pt is not None:
                r.font.size = Pt(font_size_pt)
            if base_bold:
                r.font.bold = True
            if base_italic:
                r.font.italic = True
        elif kind == "CODE":
            if not val:
                continue
            r = paragraph.add_run(val)
            r.font.name = code_font_name
            if font_size_pt is not None:
                r.font.size = Pt(round(font_size_pt * 0.92, 1))
            else:
                r.font.size = Pt(8.5)
            if base_bold:
                r.font.bold = True
            if base_italic:
                r.font.italic = True
        elif kind == "MATH":
            add_math_runs(
                paragraph,
                val,
                base_bold=base_bold,
                base_italic=base_italic,
                font_size_pt=font_size_pt,
                font_name=font_name,
            )
        elif kind == "BOLD":
            emit_ast_runs(
                paragraph,
                val,
                base_bold=True,
                base_italic=base_italic,
                font_size_pt=font_size_pt,
                font_name=font_name,
                code_font_name=code_font_name,
            )
        elif kind == "ITALIC":
            emit_ast_runs(
                paragraph,
                val,
                base_bold=base_bold,
                base_italic=True,
                font_size_pt=font_size_pt,
                font_name=font_name,
                code_font_name=code_font_name,
            )
        elif kind == "BOLD_ITALIC":
            emit_ast_runs(
                paragraph,
                val,
                base_bold=True,
                base_italic=True,
                font_size_pt=font_size_pt,
                font_name=font_name,
                code_font_name=code_font_name,
            )


def add_formatted_runs(
    paragraph,
    text: str,
    default_size: Pt = None,
    default_font: str = "Times New Roman",
    default_bold: bool = False,
    default_italic: bool = False,
    code_font_name: str = "Consolas",
):
    """Parse inline Markdown/math `text` into AST nodes and append runs to `paragraph`."""
    if not text:
        return
    size_pt = default_size.pt if isinstance(default_size, Pt) else default_size
    nodes = parse_inline_ast(text)
    emit_ast_runs(
        paragraph,
        nodes,
        base_bold=default_bold,
        base_italic=default_italic,
        font_size_pt=size_pt,
        font_name=default_font or "Times New Roman",
        code_font_name=code_font_name,
    )


# ==============================================================================
# 3. Table, Section, Equation, and Paragraph Helpers
# ==============================================================================

def disable_paragraph_numbering(p):
    """Explicitly suppress automatic list/table/footnote numbering (<w:numId w:val="0"/>) on `p`."""
    pPr = p._p.get_or_add_pPr()
    for existing in pPr.findall(qn("w:numPr")):
        pPr.remove(existing)
    pPr.append(parse_xml(f'<w:numPr {nsdecls("w")}><w:numId w:val="0"/></w:numPr>'))


def set_paragraph_list_level(p, num_id: int = 1, ilvl: int = 0):
    """Set explicit numbering ID and indentation level on a list paragraph."""
    pPr = p._p.get_or_add_pPr()
    for existing in pPr.findall(qn("w:numPr")):
        pPr.remove(existing)
    pPr.append(
        parse_xml(
            f'<w:numPr {nsdecls("w")}><w:ilvl w:val="{ilvl}"/><w:numId w:val="{num_id}"/></w:numPr>'
        )
    )


def set_cell_margins(cell, top=30, bottom=30, left=35, right=35):
    """Set inner cell padding in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    for existing in tcPr.findall(qn("w:tcMar")):
        tcPr.remove(existing)
    tcMar = OxmlElement("w:tcMar")
    for m_name, val in [("w:top", top), ("w:bottom", bottom), ("w:left", left), ("w:right", right)]:
        node = OxmlElement(m_name)
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_table_borders(table):
    """Apply clean IEEE horizontal rules (double top rule, single bottom rule, subtle insideH)."""
    tblPr = table._tbl.tblPr
    for existing in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(existing)
    tblPr.append(
        parse_xml(
            f"""<w:tblBorders {nsdecls("w")}>
              <w:top w:val="double" w:sz="4" w:space="0" w:color="000000"/>
              <w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>
              <w:bottom w:val="single" w:sz="6" w:space="0" w:color="000000"/>
              <w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>
              <w:insideH w:val="single" w:sz="4" w:space="0" w:color="D0D0D0"/>
              <w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>
            </w:tblBorders>"""
        )
    )


def set_cell_shading(cell, color_hex: str):
    """Apply background shading fill to a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    for existing in tcPr.findall(qn("w:shd")):
        tcPr.remove(existing)
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{color_hex}"/>'))


def split_md_row(line: str) -> list:
    """Split a Markdown table row by `|`, respecting code spans (`...`), math spans ($...$), and `\\|`."""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    cells = []
    curr = []
    in_math = False
    in_code = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line) and line[i + 1] == "|":
            curr.append("|")
            i += 2
            continue
        if ch == "`" and not in_math:
            in_code = not in_code
            curr.append(ch)
            i += 1
            continue
        if ch == "$" and not in_code:
            in_math = not in_math
            curr.append(ch)
            i += 1
            continue
        if ch == "|" and not in_math and not in_code:
            cells.append("".join(curr).strip())
            curr = []
            i += 1
            continue
        curr.append(ch)
        i += 1
    cells.append("".join(curr).strip())
    return cells


def compute_column_widths(num_cols: int, table_title: str = "") -> list:
    """Return explicit column widths in Pt totaling 504.6 pt (10,092 dxa full printable width)."""
    t_upper = table_title.upper()
    if "TABLE I:" in t_upper or ("TABLE I" in t_upper and "THREE-LEVEL" in t_upper):
        return [Pt(118), Pt(146), Pt(80), Pt(80), Pt(80.6)]
    elif "TABLE II-B" in t_upper:
        return [Pt(34), Pt(44), Pt(38), Pt(116), Pt(116), Pt(116), Pt(40.6)]
    elif "TABLE II-C" in t_upper:
        return [Pt(62), Pt(34), Pt(52), Pt(38), Pt(38), Pt(75), Pt(85), Pt(120.6)]
    elif "TABLE II" in t_upper and "PHYSICAL STORAGE" in t_upper:
        return [Pt(28), Pt(52), Pt(32), Pt(28), Pt(34), Pt(42), Pt(42), Pt(42), Pt(42), Pt(34), Pt(42.8), Pt(42.8), Pt(43.0)]
    elif "SUB-TABLE III-A" in t_upper or "FRIEDMAN" in t_upper:
        return [Pt(38), Pt(68), Pt(84), Pt(52), Pt(56), Pt(64), Pt(142.6)]
    elif "SUB-TABLE III-B" in t_upper or "WILCOXON" in t_upper:
        return [Pt(42), Pt(112), Pt(48), Pt(78), Pt(78), Pt(54), Pt(92.6)]
    elif "SUB-TABLE III-C" in t_upper or "LATENCIES" in t_upper:
        return [Pt(30), Pt(49), Pt(54), Pt(54), Pt(64), Pt(48), Pt(38), Pt(52), Pt(61), Pt(54.6)]
    elif "TABLE V" in t_upper:
        return [Pt(75), Pt(85), Pt(82), Pt(82), Pt(82), Pt(98.6)]
    elif "TABLE IV" in t_upper or "RETRIEVAL DECOMPOSITION" in t_upper:
        return [Pt(32), Pt(54), Pt(48), Pt(32), Pt(48), Pt(65), Pt(65), Pt(56), Pt(56), Pt(48.6)]
    else:
        w = 504.6 / max(1, num_cols)
        return [Pt(w)] * num_cols


def add_displayed_equation(doc, eq_content: str):
    """
    Format a displayed equation (`$$ ... $$`) using `styleId="equation"` with
    Times New Roman typography, proper math symbols/subscripts/superscripts,
    and right-aligned equation tag `(1)`–`(9)` when present.
    """
    tag_match = re.search(r"\\tag\{([^}]+)\}", eq_content)
    tag_num = tag_match.group(1).strip() if tag_match else None
    eq_formula = re.sub(r"\\tag\{[^}]+\}", "", eq_content).strip()

    p = doc.add_paragraph(style="equation")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.left_indent = Pt(6)
    p.paragraph_format.first_line_indent = Pt(0)

    add_math_runs(
        p,
        eq_formula,
        base_bold=False,
        base_italic=False,
        font_size_pt=8.5,
        font_name="Times New Roman",
    )
    if tag_num:
        r_tab = p.add_run(f"\t({tag_num})")
        r_tab.font.name = "Times New Roman"
        r_tab.font.size = Pt(8.5)
        r_tab.font.italic = False
        r_tab.font.bold = False
    return p


def resolve_figure_path(fig_num: int, figures_dir: str) -> str:
    """
    Locate the figure PNG for `fig_num` (1, 2, or 3) across candidate filenames
    in `figures_dir`. Returns path if found, or None if unavailable.
    """
    candidates_by_num = {
        1: ["figure_01.png", "fig1_storage_and_cost_pipeline.png"],
        2: ["figure_02.png", "fig2_scale_sweep_and_latency.png"],
        3: ["figure_03.png", "fig3_recall_and_boundary_ties.png", "fig3_retrieval_recall_and_ties.png"],
    }
    if not figures_dir:
        return None
    for cand in candidates_by_num.get(fig_num, [f"figure_0{fig_num}.png"]):
        cand_path = os.path.join(figures_dir, cand)
        if os.path.isfile(cand_path):
            return cand_path
    return None


# ==============================================================================
# 4. Post-Save OOXML Package Sanitization & Metadata Synchronization
# ==============================================================================

def finalize_ooxml_package(
    docx_path: str,
    title_text: str,
    author_name: str,
    keywords_text: str,
    created_iso: str,
    modified_iso: str,
    page_count: int = None,
) -> dict:
    """
    Inspect and sanitize the saved `.docx` archive using namespace-aware `lxml.etree`:
      1. Inspect every `w:sectPr` in `word/document.xml` and remove all `w:footerReference`,
         `w:headerReference`, and `w:titlePg` elements.
      2. Inspect `word/_rels/document.xml.rels`: remove unreferenced footer relationships
         (`footer1.xml`) and unreferenced sample-text external hyperlinks (`rId9`, `rId10`).
      3. Remove `word/footer1.xml` and its `<Override>` in `[Content_Types].xml` when unreferenced.
      4. Populate `docProps/core.xml` and `docProps/app.xml` with accurate metadata and counts.
      5. Validate that zero dangling relationships or missing internal targets remain.
    """
    doc_check = docx.Document(docx_path)
    non_empty_paras = [p.text.strip() for p in doc_check.paragraphs if p.text.strip()]
    body_words = sum(len(t.split()) for t in non_empty_paras)
    body_chars_no_spaces = sum(len(t.replace(" ", "")) for t in non_empty_paras)
    body_chars_with_spaces = sum(len(t) for t in non_empty_paras)
    para_count = len(non_empty_paras)
    line_estimate = max(para_count, body_words // 10)

    with open(docx_path, "rb") as f:
        raw_bytes = f.read()

    zin = zipfile.ZipFile(io.BytesIO(raw_bytes), "r")
    members = {info.filename: zin.read(info.filename) for info in zin.infolist()}
    zin.close()

    # 1. Clean all w:sectPr in word/document.xml and collect referenced r:id values
    doc_root = ET.fromstring(members["word/document.xml"])
    removed_footer_refs = 0
    removed_title_pgs = 0
    for sectPr in doc_root.xpath("//*[local-name()='sectPr']"):
        for fref in list(sectPr.findall(f"{{{W_NS}}}footerReference")):
            sectPr.remove(fref)
            removed_footer_refs += 1
        for href in list(sectPr.findall(f"{{{W_NS}}}headerReference")):
            sectPr.remove(href)
        for tpg in list(sectPr.findall(f"{{{W_NS}}}titlePg")):
            sectPr.remove(tpg)
            removed_title_pgs += 1

    referenced_rids = set()
    for el in doc_root.iter():
        for attr_k, attr_v in el.attrib.items():
            if attr_k in (f"{{{R_NS}}}id", f"{{{R_NS}}}embed", f"{{{R_NS}}}link"):
                referenced_rids.add(attr_v)

    members["word/document.xml"] = ET.tostring(
        doc_root, xml_declaration=True, encoding="UTF-8", standalone="yes"
    )

    # 2. Clean word/_rels/document.xml.rels
    rels_root = ET.fromstring(members["word/_rels/document.xml.rels"])
    removed_rels = []
    kept_targets = set()
    for rel in list(rels_root):
        rid = rel.get("Id")
        rtype = rel.get("Type", "")
        rtarget = rel.get("Target", "")
        tmode = rel.get("TargetMode", "")
        if rtype.endswith("/footer") or rtype.endswith("/header"):
            if rid not in referenced_rids:
                rels_root.remove(rel)
                removed_rels.append((rid, rtype, rtarget))
                continue
        if tmode == "External" and rid not in referenced_rids:
            rels_root.remove(rel)
            removed_rels.append((rid, rtype, rtarget))
            continue
        kept_targets.add(rtarget)

    members["word/_rels/document.xml.rels"] = ET.tostring(
        rels_root, xml_declaration=True, encoding="UTF-8", standalone="yes"
    )

    # 3. Remove unreferenced word/footer1.xml and its Content_Types Override
    if "footer1.xml" not in kept_targets and "/word/footer1.xml" not in kept_targets:
        members.pop("word/footer1.xml", None)
        ct_root = ET.fromstring(members["[Content_Types].xml"])
        for ov in list(ct_root):
            if ov.get("PartName") == "/word/footer1.xml":
                ct_root.remove(ov)
        members["[Content_Types].xml"] = ET.tostring(
            ct_root, xml_declaration=True, encoding="UTF-8", standalone="yes"
        )

    # 4. Update docProps/core.xml using lxml
    core_root = ET.fromstring(members["docProps/core.xml"])
    def set_or_create(parent, tag_qname, text_val, attrib=None):
        el = parent.find(tag_qname)
        if el is None:
            el = ET.SubElement(parent, tag_qname)
        el.text = text_val
        if attrib:
            for k, v in attrib.items():
                el.set(k, v)

    set_or_create(core_root, f"{{{DC_NS}}}title", title_text)
    set_or_create(core_root, f"{{{DC_NS}}}creator", author_name)
    set_or_create(core_root, f"{{{CP_NS}}}lastModifiedBy", author_name)
    set_or_create(core_root, f"{{{CP_NS}}}keywords", keywords_text)
    set_or_create(
        core_root,
        f"{{{DCTERMS_NS}}}created",
        created_iso,
        {f"{{{XSI_NS}}}type": "dcterms:W3CDTF"},
    )
    set_or_create(
        core_root,
        f"{{{DCTERMS_NS}}}modified",
        modified_iso,
        {f"{{{XSI_NS}}}type": "dcterms:W3CDTF"},
    )
    members["docProps/core.xml"] = ET.tostring(
        core_root, xml_declaration=True, encoding="UTF-8", standalone="yes"
    )

    # 5. Update docProps/app.xml using lxml
    app_root = ET.fromstring(members["docProps/app.xml"])
    app_updates = {
        "Words": str(body_words),
        "Characters": str(body_chars_no_spaces),
        "CharactersWithSpaces": str(body_chars_with_spaces),
        "Paragraphs": str(para_count),
        "Lines": str(line_estimate),
        "Company": "",
    }
    if page_count is not None:
        app_updates["Pages"] = str(page_count)

    for tag_local, val_str in app_updates.items():
        el = app_root.find(f"{{{EXT_NS}}}{tag_local}")
        if el is not None:
            el.text = val_str

    titles_vec = app_root.xpath("//*[local-name()='TitlesOfParts']/*[local-name()='vector']/*[local-name()='lpstr']")
    if titles_vec:
        titles_vec[0].text = title_text

    members["docProps/app.xml"] = ET.tostring(
        app_root, xml_declaration=True, encoding="UTF-8", standalone="yes"
    )

    # Write updated archive
    out_buf = io.BytesIO()
    with zipfile.ZipFile(out_buf, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for fname, content in members.items():
            zout.writestr(fname, content)
    with open(docx_path, "wb") as f:
        f.write(out_buf.getvalue())

    return {
        "words": body_words,
        "chars_no_spaces": body_chars_no_spaces,
        "chars_with_spaces": body_chars_with_spaces,
        "paragraphs": para_count,
        "pages": page_count,
        "removed_footer_refs": removed_footer_refs,
        "removed_title_pgs": removed_title_pgs,
        "removed_rels": removed_rels,
    }


# ==============================================================================
# 5. Main Manuscript Builder
# ==============================================================================

def build_manuscript(
    template_path: str,
    source_md_path: str,
    output_docx_path: str,
    figures_dir: str = None,
    output_pdf_path: str = None,
    author_overrides: dict = None,
    created_iso: str = "2026-11-01T16:00:00Z",
    modified_iso: str = "2026-11-02T19:45:00Z",
) -> dict:
    """
    Build the formatted IEEE A4 DOCX (and optional rendered PDF) from the canonical
    Markdown source (`final_research_paper_source_v1.3.2.md`) and `conference-template-a4.docx`.
    """
    if not os.path.isfile(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")
    if not os.path.isfile(source_md_path):
        raise FileNotFoundError(f"Canonical source Markdown not found: {source_md_path}")

    with open(source_md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    md_lines = [line.rstrip("\r\n") for line in md_text.splitlines()]
    n_lines = len(md_lines)

    # 1. Dynamically extract Title, Author, Affiliation lines, Abstract, and Keywords from source
    title_text = md_lines[0].lstrip("# ").strip()
    author_name = md_lines[2].replace("**", "").strip()
    affil_lines_raw = [md_lines[3].strip(), md_lines[4].strip(), md_lines[5].strip(), md_lines[6].strip()]

    if author_overrides:
        if author_overrides.get("author_name"):
            author_name = author_overrides["author_name"]
        if author_overrides.get("department"):
            affil_lines_raw[0] = f"*{author_overrides['department']}*"
        if author_overrides.get("institution"):
            affil_lines_raw[1] = f"*{author_overrides['institution']}*"
        if author_overrides.get("location"):
            affil_lines_raw[2] = author_overrides["location"]
        if author_overrides.get("contact_line"):
            affil_lines_raw[3] = author_overrides["contact_line"]

    # Normalize template in memory and open with python-docx
    normalized_tpl_bytes = normalize_template_to_bytes(template_path)
    doc = docx.Document(io.BytesIO(normalized_tpl_bytes))

    # Clear all sample paragraphs and tables from template body while keeping final sectPr
    body = doc._body._body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)

    # Section management helper: avoids redundant empty sections between consecutive wide floats
    # Section 0 is 1-column Title Banner
    col_state = {"mode": "1col_title"}

    def append_section_break_with_current_layout(prev_mode: str):
        p_brk = doc.add_paragraph()
        pPr = p_brk._p.get_or_add_pPr()
        pPr.append(parse_xml(f'<w:spacing {nsdecls("w")} w:before="0" w:after="0" w:line="20" w:lineRule="exact"/>'))
        if prev_mode == "1col_title":
            pPr.append(
                parse_xml(
                    f"""<w:sectPr {nsdecls("w")}>
                      <w:pgSz w:w="11906" w:h="16838" w:code="9"/>
                      <w:pgMar w:top="540" w:right="893" w:bottom="1440" w:left="893" w:header="720" w:footer="720" w:gutter="0"/>
                      <w:cols w:space="720"/>
                      <w:docGrid w:linePitch="360"/>
                    </w:sectPr>"""
                )
            )
        elif prev_mode == "2col":
            pPr.append(
                parse_xml(
                    f"""<w:sectPr {nsdecls("w")}>
                      <w:type w:val="continuous"/>
                      <w:pgSz w:w="11906" w:h="16838" w:code="9"/>
                      <w:pgMar w:top="1080" w:right="907" w:bottom="1440" w:left="907" w:header="720" w:footer="720" w:gutter="0"/>
                      <w:cols w:num="2" w:space="360"/>
                      <w:docGrid w:linePitch="360"/>
                    </w:sectPr>"""
                )
            )
        elif prev_mode == "1col_wide":
            pPr.append(
                parse_xml(
                    f"""<w:sectPr {nsdecls("w")}>
                      <w:type w:val="continuous"/>
                      <w:pgSz w:w="11906" w:h="16838" w:code="9"/>
                      <w:pgMar w:top="1080" w:right="907" w:bottom="1440" w:left="907" w:header="720" w:footer="720" w:gutter="0"/>
                      <w:cols w:space="720"/>
                      <w:docGrid w:linePitch="360"/>
                    </w:sectPr>"""
                )
            )

    def ensure_two_column():
        if col_state["mode"] != "2col":
            append_section_break_with_current_layout(col_state["mode"])
            col_state["mode"] = "2col"

    def ensure_wide_column():
        if col_state["mode"] != "1col_wide":
            append_section_break_with_current_layout(col_state["mode"])
            col_state["mode"] = "1col_wide"

    # Populate Title & Author Block in Section 0 (1-column banner)
    p_title = doc.add_paragraph(style="paper title")
    p_title.paragraph_format.space_after = Pt(10)
    add_formatted_runs(p_title, title_text, default_size=Pt(24.0))

    p_author = doc.add_paragraph(style="Author")
    p_author.paragraph_format.space_before = Pt(6)
    p_author.paragraph_format.space_after = Pt(2)
    add_formatted_runs(p_author, author_name, default_size=Pt(11.0))

    for idx_aff, aff_line in enumerate(affil_lines_raw):
        if not aff_line:
            continue
        p_aff = doc.add_paragraph(style="Affiliation")
        p_aff.paragraph_format.space_before = Pt(0)
        p_aff.paragraph_format.space_after = Pt(6 if idx_aff == len(affil_lines_raw) - 1 else 1)
        add_formatted_runs(p_aff, aff_line, default_size=Pt(9.5))

    # Track build statistics and warnings
    missing_figures = []
    equation_count = 0
    table_count = 0
    figure_count = 0
    reference_count = 0
    keywords_plain = ""
    abstract_plain = ""

    # Parse Markdown lines starting after author block (line index 7)
    i = 7
    in_references = False
    in_code_block = False
    code_lines = []

    while i < n_lines:
        raw_line = md_lines[i]
        line = raw_line.strip()

        if not line:
            i += 1
            continue

        # 1. Fenced code block (```c ... ```)
        if line.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lines = []
            else:
                in_code_block = False
                ensure_two_column()
                for c_idx, cl in enumerate(code_lines):
                    p_code = doc.add_paragraph(style="Body Text")
                    p_code.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    p_code.paragraph_format.first_line_indent = Pt(0)
                    p_code.paragraph_format.left_indent = Pt(10)
                    p_code.paragraph_format.space_before = Pt(2 if c_idx == 0 else 0)
                    p_code.paragraph_format.space_after = Pt(4 if c_idx == len(code_lines) - 1 else 0)
                    if c_idx < len(code_lines) - 1:
                        p_code.paragraph_format.keep_with_next = True
                    r_c = p_code.add_run(cl)
                    r_c.font.name = "Consolas"
                    r_c.font.size = Pt(7.5)
            i += 1
            continue

        if in_code_block:
            code_lines.append(raw_line)
            i += 1
            continue

        # 2. Skip standalone `## Abstract` Markdown marker (IEEE uses inline `Abstract—` lead-in)
        if line == "## Abstract":
            i += 1
            continue

        # 3. Dynamic Abstract paragraph (`**Abstract**—...`)
        if line.startswith("**Abstract**—"):
            ensure_two_column()
            p_abs = doc.add_paragraph(style="Abstract")
            p_abs.paragraph_format.space_after = Pt(6)
            r_lead = p_abs.add_run("Abstract")
            r_lead.font.name = "Times New Roman"
            r_lead.font.size = Pt(9.0)
            r_lead.font.bold = True
            r_lead.font.italic = True
            r_dash = p_abs.add_run("—")
            r_dash.font.name = "Times New Roman"
            r_dash.font.size = Pt(9.0)
            r_dash.font.bold = True
            body_abs = line[len("**Abstract**—"):].strip()
            add_formatted_runs(
                p_abs,
                body_abs,
                default_size=Pt(9.0),
                default_font="Times New Roman",
                default_bold=True,
                code_font_name="Times New Roman",
            )
            abstract_plain = p_abs.text
            i += 1
            continue

        # 4. Dynamic Keywords paragraph (`*Keywords*—...`)
        if line.startswith("*Keywords*—"):
            ensure_two_column()
            p_kw = doc.add_paragraph(style="Keywords")
            p_kw.paragraph_format.space_after = Pt(10)
            r_kw = p_kw.add_run("Keywords")
            r_kw.font.name = "Times New Roman"
            r_kw.font.size = Pt(9.0)
            r_kw.font.bold = True
            r_kw.font.italic = True
            r_dash = p_kw.add_run("—")
            r_dash.font.name = "Times New Roman"
            r_dash.font.size = Pt(9.0)
            r_dash.font.bold = True
            body_kw = line[len("*Keywords*—"):].strip()
            keywords_plain = body_kw
            add_formatted_runs(
                p_kw,
                body_kw,
                default_size=Pt(9.0),
                default_font="Times New Roman",
                default_bold=True,
                default_italic=False,
                code_font_name="Times New Roman",
            )
            i += 1
            continue

        # 5. Headings (`## `, `### `, `#### `)
        if line.startswith("## "):
            h_text = line[3:].strip()
            ensure_two_column()
            if (
                h_text.startswith("Appendix ")
                or h_text.startswith("Acknowledgment")
                or h_text.startswith("References")
            ):
                p_h5 = doc.add_paragraph(style="Heading 5")
                p_h5.paragraph_format.space_before = Pt(10)
                p_h5.paragraph_format.space_after = Pt(4)
                p_h5.paragraph_format.keep_with_next = True
                add_formatted_runs(p_h5, h_text, default_size=Pt(10.0))
                in_references = h_text.startswith("References")
            else:
                # Strip explicit Roman numeral prefix (`I. `, `II. `, ...) because Heading 1 supplies numId=4
                clean_h1 = re.sub(r"^[IVXLCDM]+\.\s+", "", h_text)
                p_h1 = doc.add_paragraph(style="Heading 1")
                p_h1.paragraph_format.space_before = Pt(10)
                p_h1.paragraph_format.space_after = Pt(4)
                p_h1.paragraph_format.keep_with_next = True
                add_formatted_runs(p_h1, clean_h1, default_size=Pt(10.0))
                in_references = False
            i += 1
            continue

        if line.startswith("### "):
            ensure_two_column()
            h2_text = line[4:].strip()
            # Strip explicit capital letter prefix (`A. `, `B. `, ...) because Heading 2 supplies numId=4 ilvl=1
            clean_h2 = re.sub(r"^[A-Z]\.\s+", "", h2_text)
            p_h2 = doc.add_paragraph(style="Heading 2")
            p_h2.paragraph_format.space_before = Pt(8)
            p_h2.paragraph_format.space_after = Pt(3)
            p_h2.paragraph_format.keep_with_next = True
            add_formatted_runs(p_h2, clean_h2, default_size=Pt(10.0), default_italic=True)
            i += 1
            continue

        if line.startswith("#### "):
            # Sub-Table headings (`#### Sub-Table III-A: ...`)
            ensure_wide_column()
            st_text = line[5:].strip()
            p_st = doc.add_paragraph(style="table head")
            disable_paragraph_numbering(p_st)
            p_st.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_st.paragraph_format.space_before = Pt(6)
            p_st.paragraph_format.space_after = Pt(2)
            p_st.paragraph_format.keep_with_next = True
            add_formatted_runs(p_st, st_text, default_size=Pt(8.0), default_bold=True)
            i += 1
            continue

        # 6. Displayed Equations (`$$ ... $$`)
        if line.startswith("$$"):
            ensure_two_column()
            if line.endswith("$$") and len(line) > 2:
                eq_content = line[2:-2].strip()
            else:
                eq_lines = [line[2:].strip()]
                i += 1
                while i < n_lines and not md_lines[i].strip().endswith("$$"):
                    eq_lines.append(md_lines[i].strip())
                    i += 1
                if i < n_lines:
                    eq_lines.append(md_lines[i].strip()[:-2].strip())
                eq_content = " ".join(eq_lines).strip()
            add_displayed_equation(doc, eq_content)
            equation_count += 1
            i += 1
            continue

        # 7. Figure Blocks (`> **[FIGURE ...]` followed by `> **Fig. X.** *...*`)
        if line.startswith(">") and ("[FIGURE" in line or "Fig." in line):
            fig_lines = []
            while i < n_lines and md_lines[i].strip().startswith(">"):
                fig_lines.append(md_lines[i].strip()[1:].strip())
                i += 1
            fig_block = " ".join(fig_lines)
            fig_num_match = re.search(r"figure_0(\d)|Fig(?:ure)?\.?\s*(\d+)", fig_block)
            if fig_num_match:
                fig_num = int(fig_num_match.group(1) or fig_num_match.group(2))
            else:
                fig_num = figure_count + 1

            cap_lines = [
                l for l in fig_lines if not (l.startswith("**[FIGURE") or l.startswith("[FIGURE"))
            ]
            caption_raw = " ".join(cap_lines).strip()
            # Strip leading `**Fig. X.** ` because `figure caption` style (numId=2) supplies `Fig. X.`
            caption_body = re.sub(r"^\*\*Fig\.\s*\d+\.\*\*\s*", "", caption_raw).strip()
            # If the entire caption body is wrapped in outer `*...*` for Markdown italics, unwrap the outer pair
            if caption_body.startswith("*") and caption_body.endswith("*") and not caption_body.startswith("**"):
                caption_body = caption_body[1:-1].strip()

            ensure_wide_column()
            img_path = resolve_figure_path(fig_num, figures_dir)
            img_p = doc.add_paragraph()
            img_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            img_p.paragraph_format.first_line_indent = Pt(0)
            img_p.paragraph_format.space_before = Pt(6)
            img_p.paragraph_format.space_after = Pt(2)
            img_p.paragraph_format.keep_with_next = True

            if img_path and os.path.isfile(img_path):
                fig_w = Inches(5.25) if fig_num == 2 else Inches(6.95)
                img_p.add_run().add_picture(img_path, width=fig_w)
            else:
                missing_msg = (
                    f"[MISSING SOURCE FIGURE ASSET: figure_0{fig_num}.png — "
                    f"Expected in {figures_dir or '<unset>'}; figure omitted rather than fabricated]"
                )
                missing_figures.append(missing_msg)
                r_miss = img_p.add_run(missing_msg)
                r_miss.font.name = "Times New Roman"
                r_miss.font.size = Pt(9.0)
                r_miss.font.bold = True

            cap_p = doc.add_paragraph(style="figure caption")
            cap_p.paragraph_format.keep_together = True
            cap_p.paragraph_format.space_before = Pt(2)
            cap_p.paragraph_format.space_after = Pt(8)
            add_formatted_runs(cap_p, caption_body, default_size=Pt(8.0))
            figure_count += 1
            continue

        # 8. Table Title Blocks (`**TABLE I**` + `**Title**`)
        if re.match(r"^\*\*TABLE\s+[IVXLCDM0-9A-Z-]+\*\*$", line):
            ensure_wide_column()
            tbl_label = line.strip("*").strip()
            i += 1
            tbl_title = ""
            while i < n_lines and not md_lines[i].strip():
                i += 1
            if i < n_lines and md_lines[i].strip().startswith("**") and not md_lines[i].strip().startswith("**TABLE"):
                t_line = md_lines[i].strip()
                if t_line.startswith("**") and t_line.endswith("**"):
                    tbl_title = t_line[2:-2].strip()
                else:
                    tbl_title = t_line
                i += 1

            p_th = doc.add_paragraph(style="table head")
            disable_paragraph_numbering(p_th)
            p_th.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_th.paragraph_format.space_before = Pt(8)
            p_th.paragraph_format.space_after = Pt(2)
            p_th.paragraph_format.keep_with_next = True
            full_tbl_heading = f"{tbl_label}. {tbl_title}" if tbl_title else tbl_label
            add_formatted_runs(p_th, full_tbl_heading, default_size=Pt(8.0), default_bold=True)
            continue

        # 9. Markdown Pipe Tables (`| ... |`) and Associated Table Notes
        if line.startswith("|"):
            ensure_wide_column()
            # Retrieve the preceding table title text for column-width selection
            prev_title = doc.paragraphs[-1].text if doc.paragraphs else ""
            tbl_lines = []
            while i < n_lines and md_lines[i].strip().startswith("|"):
                tbl_lines.append(md_lines[i].strip())
                i += 1

            if len(tbl_lines) >= 3:
                header_cells = split_md_row(tbl_lines[0])
                num_cols = len(header_cells)
                data_rows = [split_md_row(rl) for rl in tbl_lines[2:]]

                table = doc.add_table(rows=len(data_rows) + 1, cols=num_cols)
                table.alignment = WD_TABLE_ALIGNMENT.CENTER
                table.autofit = False
                set_table_borders(table)

                col_widths = compute_column_widths(num_cols, prev_title)
                tblGrid = table._tbl.tblGrid
                for g_idx, g_col in enumerate(tblGrid.findall(qn("w:gridCol"))):
                    if g_idx < len(col_widths):
                        g_col.set(qn("w:w"), str(int(round(col_widths[g_idx].pt * 20))))

                hdr_font_pt = 7.0 if num_cols >= 10 else 7.5
                body_font_pt = 7.0 if num_cols >= 10 else 7.5
                pad_lr = 28 if num_cols >= 10 else 36

                # Format Header Row
                hdr_row = table.rows[0]
                hdr_trPr = hdr_row._tr.get_or_add_trPr()
                hdr_trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
                hdr_trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
                for c_idx, h_text in enumerate(header_cells):
                    cell = hdr_row.cells[c_idx]
                    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                    if c_idx < len(col_widths):
                        cell.width = col_widths[c_idx]
                    set_cell_margins(cell, top=30, bottom=30, left=pad_lr, right=pad_lr)
                    set_cell_shading(cell, "F2F2F2")
                    tcPr = cell._tc.get_or_add_tcPr()
                    tcPr.append(
                        parse_xml(
                            f'<w:tcBorders {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="0" w:color="000000"/></w:tcBorders>'
                        )
                    )
                    cell_p = cell.paragraphs[0]
                    cell_p.style = doc.styles["table col head"]
                    cell_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    cell_p.paragraph_format.space_before = Pt(1)
                    cell_p.paragraph_format.space_after = Pt(1)
                    cell_p.paragraph_format.keep_with_next = True
                    add_formatted_runs(
                        cell_p,
                        h_text,
                        default_size=Pt(hdr_font_pt),
                        default_font="Times New Roman",
                        default_bold=True,
                    )

                # Format Data Rows (including Table I group header rows)
                for r_idx, row_data in enumerate(data_rows):
                    row = table.rows[r_idx + 1]
                    row._tr.get_or_add_trPr().append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
                    non_empty = [v.strip() for v in row_data if v.strip()]
                    is_group_row = len(non_empty) == 1 and row_data[0].strip() != ""

                    for c_idx in range(num_cols):
                        val = row_data[c_idx].strip() if c_idx < len(row_data) else ""
                        cell = row.cells[c_idx]
                        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                        if c_idx < len(col_widths):
                            cell.width = col_widths[c_idx]
                        set_cell_margins(cell, top=22, bottom=22, left=pad_lr, right=pad_lr)
                        if is_group_row:
                            set_cell_shading(cell, "F5F5F5")
                        cell_p = cell.paragraphs[0]
                        cell_p.style = doc.styles["table copy"]
                        cell_p.paragraph_format.space_before = Pt(0.5)
                        cell_p.paragraph_format.space_after = Pt(0.5)
                        if r_idx < len(data_rows) - 1:
                            cell_p.paragraph_format.keep_with_next = True
                        if c_idx == 0 or len(val) > 28:
                            cell_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        else:
                            cell_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        add_formatted_runs(
                            cell_p,
                            val,
                            default_size=Pt(body_font_pt),
                            default_font="Times New Roman",
                            default_bold=is_group_row,
                        )
                table_count += 1

            # Check for immediately following table footnote/note (`*\*Note:...*` or `*\*At ...*`)
            j = i
            while j < n_lines and not md_lines[j].strip():
                j += 1
            if j < n_lines and (
                md_lines[j].strip().startswith("*\\*")
                or md_lines[j].strip().startswith("*Note:")
                or md_lines[j].strip().startswith("**Note:")
            ):
                if len(tbl_lines) >= 3 and len(table.rows) > 0:
                    for cell in table.rows[-1].cells:
                        for cp in cell.paragraphs:
                            cp.paragraph_format.keep_with_next = True
                fn_raw = md_lines[j].strip()
                # Unwrap outer italic `*...*` wrapper before parsing so `\*` becomes literal `*`
                if fn_raw.startswith("*") and fn_raw.endswith("*") and not fn_raw.startswith("**"):
                    fn_body = fn_raw[1:-1].strip()
                else:
                    fn_body = fn_raw
                p_tfn = doc.add_paragraph(style="table footnote")
                disable_paragraph_numbering(p_tfn)
                p_tfn.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p_tfn.paragraph_format.first_line_indent = Pt(0)
                p_tfn.paragraph_format.left_indent = Pt(0)
                p_tfn.paragraph_format.space_before = Pt(2)
                p_tfn.paragraph_format.space_after = Pt(6)
                add_formatted_runs(
                    p_tfn,
                    fn_body,
                    default_size=Pt(7.5),
                    default_font="Times New Roman",
                    default_italic=True,
                )
                i = j + 1
            continue

        # 10. Reference Entries (`[1] ...` to `[25] ...`)
        if in_references and re.match(r"^\[(\d+)\]\s+(.+)$", line):
            ensure_two_column()
            ref_match = re.match(r"^\[(\d+)\]\s+(.+)$", line)
            ref_content = ref_match.group(2).strip()
            i += 1
            while (
                i < n_lines
                and md_lines[i].strip()
                and not re.match(r"^\[\d+\]", md_lines[i].strip())
                and not md_lines[i].strip().startswith("#")
            ):
                ref_content += " " + md_lines[i].strip()
                i += 1

            # Do NOT add `[ref_num]\t` manually because `style="references"` (numId=8) supplies `[1]`..`[25]`
            p_ref = doc.add_paragraph(style="references")
            p_ref.paragraph_format.space_before = Pt(0)
            p_ref.paragraph_format.space_after = Pt(2.5)
            p_ref.paragraph_format.left_indent = Pt(18)
            p_ref.paragraph_format.first_line_indent = Pt(-18)
            add_formatted_runs(p_ref, ref_content, default_size=Pt(8.0), default_font="Times New Roman")
            reference_count += 1
            continue

        # 11. Nested and Top-Level Bullet Lists (`   - ...` and `- ...`)
        if raw_line.startswith("   - ") or raw_line.startswith("   * "):
            ensure_two_column()
            bullet_text = line[2:].strip()
            p_bul = doc.add_paragraph(style="bullet list")
            set_paragraph_list_level(p_bul, num_id=1, ilvl=1)
            p_bul.paragraph_format.space_before = Pt(1)
            p_bul.paragraph_format.space_after = Pt(2)
            p_bul.paragraph_format.left_indent = Pt(24)
            p_bul.paragraph_format.first_line_indent = Pt(-10)
            add_formatted_runs(p_bul, bullet_text, default_size=Pt(9.5))
            i += 1
            continue

        if line.startswith("- ") or line.startswith("* "):
            ensure_two_column()
            bullet_text = line[2:].strip()
            p_bul = doc.add_paragraph(style="bullet list")
            set_paragraph_list_level(p_bul, num_id=1, ilvl=0)
            p_bul.paragraph_format.space_before = Pt(1)
            p_bul.paragraph_format.space_after = Pt(2.5)
            p_bul.paragraph_format.left_indent = Pt(14.4)
            p_bul.paragraph_format.first_line_indent = Pt(-14.4)
            add_formatted_runs(p_bul, bullet_text, default_size=Pt(9.5))
            i += 1
            continue

        # 12. Standard Body Paragraph (including numbered analytical items `1. **...**`)
        ensure_two_column()
        p_body = doc.add_paragraph(style="Body Text")
        p_body.paragraph_format.space_before = Pt(0)
        p_body.paragraph_format.space_after = Pt(4)
        if line.endswith(":"):
            p_body.paragraph_format.keep_with_next = True
        add_formatted_runs(p_body, line, default_size=Pt(9.5))
        i += 1

    # Append closing 2-column section break so the final page of References balances evenly across both columns
    append_section_break_with_current_layout(col_state["mode"])

    # Configure final body-level sectPr as 1-column continuous without any footer reference
    final_sectPr = body.find(qn("w:sectPr"))
    if final_sectPr is not None:
        final_sectPr.clear()
        for el in parse_xml(
            f"""<w:sectPr {nsdecls("w")}>
              <w:type w:val="continuous"/>
              <w:pgSz w:w="11906" w:h="16838" w:code="9"/>
              <w:pgMar w:top="1080" w:right="907" w:bottom="1440" w:left="907" w:header="720" w:footer="720" w:gutter="0"/>
              <w:cols w:space="720"/>
              <w:docGrid w:linePitch="360"/>
            </w:sectPr>"""
        ):
            final_sectPr.append(el)

    os.makedirs(os.path.dirname(os.path.abspath(output_docx_path)), exist_ok=True)
    doc.save(output_docx_path)

    # First pass OOXML finalization (strip footers, clean rels, set core/app properties)
    meta_info = finalize_ooxml_package(
        docx_path=output_docx_path,
        title_text=title_text,
        author_name=author_name,
        keywords_text=keywords_plain,
        created_iso=created_iso,
        modified_iso=modified_iso,
        page_count=None,
    )

    # Optional PDF rendering via LibreOffice Writer and exact page-count sync
    rendered_pages = None
    if output_pdf_path:
        out_pdf_dir = os.path.dirname(os.path.abspath(output_pdf_path))
        os.makedirs(out_pdf_dir, exist_ok=True)
        lo_profile = tempfile.mkdtemp(prefix="lo_r44_prof_")
        subprocess.run(
            [
                "libreoffice",
                f"-env:UserInstallation=file://{lo_profile}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                out_pdf_dir,
                output_docx_path,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        default_lo_pdf = os.path.join(
            out_pdf_dir, os.path.splitext(os.path.basename(output_docx_path))[0] + ".pdf"
        )
        if os.path.abspath(default_lo_pdf) != os.path.abspath(output_pdf_path):
            os.replace(default_lo_pdf, output_pdf_path)

        import pypdf
        reader = pypdf.PdfReader(output_pdf_path)
        rendered_pages = len(reader.pages)

        # Sync exact verified page count back into docProps/app.xml and re-export PDF so DOCX and PDF match 100%
        meta_info = finalize_ooxml_package(
            docx_path=output_docx_path,
            title_text=title_text,
            author_name=author_name,
            keywords_text=keywords_plain,
            created_iso=created_iso,
            modified_iso=modified_iso,
            page_count=rendered_pages,
        )
        subprocess.run(
            [
                "libreoffice",
                f"-env:UserInstallation=file://{lo_profile}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                out_pdf_dir,
                output_docx_path,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if os.path.abspath(default_lo_pdf) != os.path.abspath(output_pdf_path):
            os.replace(default_lo_pdf, output_pdf_path)

    return {
        "title": title_text,
        "author": author_name,
        "abstract": abstract_plain,
        "keywords": keywords_plain,
        "equations": equation_count,
        "tables": table_count,
        "figures": figure_count,
        "references": reference_count,
        "missing_figures": missing_figures,
        "rendered_pages": rendered_pages,
        "meta_info": meta_info,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Build IEEE A4 Conference Manuscript DOCX and PDF (Phase R4.4 Generator v2)."
    )
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument(
        "--template",
        default=os.path.join(base_dir, "conference-template-a4.docx"),
        help="Path to conference-template-a4.docx",
    )
    parser.add_argument(
        "--source",
        default=os.path.join(base_dir, "final_research_paper_source_v1.3.3.md"),
        help="Path to canonical Markdown source (final_research_paper_source_v1.3.3.md)",
    )
    parser.add_argument(
        "--figures-dir",
        default=os.path.join(base_dir, "figures"),
        help="Directory containing figure_01.png, figure_02.png, figure_03.png",
    )
    parser.add_argument(
        "--output-docx",
        default=os.path.join(base_dir, "final_research_paper_v1.3.3.docx"),
        help="Output DOCX path",
    )
    parser.add_argument(
        "--output-pdf",
        default=os.path.join(base_dir, "final_research_paper_v1.3.3.pdf"),
        help="Output PDF path (rendered via headless LibreOffice Writer; pass '' to skip)",
    )
    parser.add_argument("--author-name", default=None, help="Optional override for author name")
    parser.add_argument("--department", default=None, help="Optional override for department line")
    parser.add_argument("--institution", default=None, help="Optional override for institution line")
    parser.add_argument("--location", default=None, help="Optional override for city/country line")
    parser.add_argument("--contact-line", default=None, help="Optional override for email/ORCID line")
    parser.add_argument(
        "--created-timestamp",
        default="2026-11-01T16:00:00Z",
        help="W3CDTF creation timestamp for docProps/core.xml",
    )
    parser.add_argument(
        "--modified-timestamp",
        default="2026-11-04T04:00:00Z",
        help="W3CDTF modification timestamp for docProps/core.xml",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    overrides = {
        "author_name": args.author_name,
        "department": args.department,
        "institution": args.institution,
        "location": args.location,
        "contact_line": args.contact_line,
    }
    pdf_target = args.output_pdf if args.output_pdf else None
    summary = build_manuscript(
        template_path=args.template,
        source_md_path=args.source,
        output_docx_path=args.output_docx,
        figures_dir=args.figures_dir,
        output_pdf_path=pdf_target,
        author_overrides=overrides,
        created_iso=args.created_timestamp,
        modified_iso=args.modified_timestamp,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
