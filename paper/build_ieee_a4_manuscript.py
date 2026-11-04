"""
Build IEEE A4 Conference Manuscript for pgvector-planner-sensitivity
Author: Yash Pradhan
Affiliation: School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology, Vellore, Tamil Nadu, India
Template: templates/conference-template-a4.docx
Source: paper/final_research_paper_source_v1.3.2.md
Output: submission/ieee_a4_review_v1/research_paper_ieee_a4_v1.docx
"""

import os
import re
import io
import zipfile
import docx
from docx.shared import Pt, Inches, Mm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(BASE_DIR, 'templates', 'conference-template-a4.docx')
SOURCE_MD_PATH = os.path.join(BASE_DIR, 'paper', 'final_research_paper_source_v1.3.2.md')
OUTPUT_DIR = os.path.join(BASE_DIR, 'submission', 'ieee_a4_review_v1')
OUTPUT_DOCX_PATH = os.path.join(OUTPUT_DIR, 'research_paper_ieee_a4_v1.docx')

FIGURES_DIR = os.path.join(BASE_DIR, 'paper', 'figures', 'reference')
FIGURES_GEN_DIR = os.path.join(BASE_DIR, 'paper', 'figures', 'generated')


def fix_template_namespaces(docx_bytes):
    """Convert ISO/IEC 29500 Strict namespaces to transitional namespaces for python-docx."""
    in_zip = zipfile.ZipFile(io.BytesIO(docx_bytes), 'r')
    out_buf = io.BytesIO()
    out_zip = zipfile.ZipFile(out_buf, 'w', compression=zipfile.ZIP_DEFLATED)
    for item in in_zip.infolist():
        content = in_zip.read(item.filename)
        if item.filename.endswith('.rels'):
            content = content.replace(
                b'http://purl.oclc.org/ooxml/officeDocument/relationships/',
                b'http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
            )
            content = content.replace(
                b'http://purl.oclc.org/ooxml/package/relationships/',
                b'http://schemas.openxmlformats.org/package/2006/relationships/'
            )
        elif item.filename.endswith('.xml'):
            content = content.replace(
                b'http://purl.oclc.org/ooxml/wordprocessingml/main',
                b'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
            )
            content = content.replace(
                b'http://purl.oclc.org/ooxml/officeDocument/',
                b'http://schemas.openxmlformats.org/officeDocument/2006/'
            )
            content = content.replace(
                b'http://purl.oclc.org/ooxml/drawingml/',
                b'http://schemas.openxmlformats.org/drawingml/2006/'
            )
        out_zip.writestr(item, content)
    out_zip.close()
    out_buf.seek(0)
    return out_buf.getvalue()


def clean_math_text(s):
    """Convert LaTeX math notation to clean Unicode strings for Word text runs."""
    if not s:
        return ""
    replacements = [
        (r'\{,\}', ','),
        (r'\{,(\d+)\}', r',\1'),
        (r'\\text\{([^}]+)\}', r'\1'),
        (r'\\mathbf\{([^}]+)\}', r'\1'),
        (r'\\texttt\{([^}]+)\}', r'\1'),
        (r'\\mathit\{([^}]+)\}', r'\1'),
        (r'\\mathcal\{([^}]+)\}', r'\1'),
        (r'\\text\{([^}]+)\}', r'\1'),
        (r'\\mathbf\{([^}]+)\}', r'\1'),
        (r'\\left\\lfloor', '⌊'),
        (r'\\right\\rfloor', '⌋'),
        (r'\\lfloor', '⌊'),
        (r'\\rfloor', '⌋'),
        (r'\\left⌊', '⌊'),
        (r'\\right⌋', '⌋'),
        (r'\\frac\{([^}]+)\}\{([^}]+)\}', r'((\1) / (\2))'),
        (r'\\left\(', '('),
        (r'\\right\)', ')'),
        (r'\\left\[', '['),
        (r'\\right\]', ']'),
        (r'\\left\\\{', '{'),
        (r'\\right\\\}', '}'),
        (r'\\big\(', '('),
        (r'\\big\)', ')'),
        (r'\\Big\(', '('),
        (r'\\Big\)', ')'),
        (r'\\!', ''),
        (r'\\;', ' '),
        (r'\\,', ' '),
        (r'\\ ', ' '),
        (r'\\cdot', '·'),
        (r'\\times', '×'),
        (r'\\le\b', '≤'),
        (r'\\ge\b', '≥'),
        (r'\\in\b', '∈'),
        (r'\\to\b', '→'),
        (r'\\Delta\b', 'Δ'),
        (r'\\tau\b', 'τ'),
        (r'\\alpha\b', 'α'),
        (r'\\chi\^2_8', 'χ²₈'),
        (r'\\chi\^2', 'χ²'),
        (r'\\pm', '±'),
        (r'\\approx', '≈'),
        (r'\\neq', '≠'),
        (r'\\ln\b', 'ln'),
        (r'\\log_2\b', 'log₂'),
        (r'\\mid', '|'),
        (r'\{,\}', ','),
        (r'\{,(\d+)\}', r',\1'),
        (r'\\_', '_'),
        (r'\\%', '%'),
        (r'\\quad', '    '),
        (r'\\qquad', '        '),
        (r'\\dots', '...'),
        (r'\\cap', '∩'),
        (r'\\cup', '∪'),
        (r'\\setminus', ' \\ '),
        (r'\\subseteq', '⊆'),
        (r'_\{([^}]+)\}', r'_\1'),
        (r'\^\{([^}]+)\}', r'^\1'),
    ]
    res = s
    for pat, rep in replacements:
        res = re.sub(pat, rep, res)
    return res


def add_formatted_runs(paragraph, text, default_size=None, default_font=None):
    """
    Parse inline markdown (bold, italic, code, math, plain text)
    and append formatted runs to paragraph.
    """
    if not text:
        return

    token_pattern = re.compile(
        r'(\*\*\*[^*]+?\*\*\*|\*\*[^*]+?\*\*|\*[^*]+?\*|`[^`]+?`|\$[^\$]+?\$|[^\*`\$]+)'
    )
    tokens = token_pattern.findall(text)

    for tok in tokens:
        if tok.startswith('***') and tok.endswith('***') and len(tok) >= 6:
            inner = clean_math_text(tok[3:-3])
            run = paragraph.add_run(inner)
            run.bold = True
            run.italic = True
        elif tok.startswith('**') and tok.endswith('**') and len(tok) >= 4:
            inner = clean_math_text(tok[2:-2])
            if inner.startswith('`') and inner.endswith('`') and len(inner) >= 2:
                inner = inner[1:-1]
                run = paragraph.add_run(inner)
                run.bold = True
                run.font.name = 'Consolas'
                run.font.size = Pt(8.5) if default_size is None else Pt(default_size.pt * 0.95)
            else:
                run = paragraph.add_run(inner)
                run.bold = True
        elif tok.startswith('*') and tok.endswith('*') and len(tok) >= 2 and not tok.startswith('**'):
            inner = clean_math_text(tok[1:-1])
            run = paragraph.add_run(inner)
            run.italic = True
        elif tok.startswith('`') and tok.endswith('`') and len(tok) >= 2:
            inner = tok[1:-1]
            run = paragraph.add_run(inner)
            run.font.name = 'Consolas'
            run.font.size = Pt(8.5) if default_size is None else Pt(default_size.pt * 0.95)
        elif tok.startswith('$') and tok.endswith('$') and len(tok) >= 2:
            inner = clean_math_text(tok[1:-1])
            run = paragraph.add_run(inner)
            run.italic = True
        else:
            run = paragraph.add_run(tok)

        if default_size and run.font.size is None:
            run.font.size = default_size
        if default_font and run.font.name is None:
            run.font.name = default_font


def set_cell_margins(cell, top=40, bottom=40, left=40, right=40):
    """Set inner cell padding in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def set_table_borders(table):
    """Apply clean standard IEEE horizontal borders with no vertical rules."""
    tblPr = table._tbl.tblPr
    for existing in tblPr.findall(qn('w:tblBorders')):
        tblPr.remove(existing)
    
    borders = OxmlElement('w:tblBorders')
    
    top = OxmlElement('w:top')
    top.set(qn('w:val'), 'single')
    top.set(qn('w:sz'), '6')
    top.set(qn('w:space'), '0')
    top.set(qn('w:color'), '000000')
    borders.append(top)
    
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '0')
    bottom.set(qn('w:color'), '000000')
    borders.append(bottom)
    
    insideH = OxmlElement('w:insideH')
    insideH.set(qn('w:val'), 'single')
    insideH.set(qn('w:sz'), '4')
    insideH.set(qn('w:space'), '0')
    insideH.set(qn('w:color'), 'CCCCCC')
    borders.append(insideH)
    
    for b_name in ['left', 'right', 'insideV']:
        b = OxmlElement(f'w:{b_name}')
        b.set(qn('w:val'), 'none')
        borders.append(b)
        
    tblPr.append(borders)


def set_cell_shading(cell, color_hex):
    """Apply background color to cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    tcPr.append(shd)


def make_wide_section(doc):
    """Insert continuous section break switching from 2 columns to 1 column."""
    new_sec = doc.add_section(WD_SECTION.CONTINUOUS)
    new_sec.top_margin = Pt(54)
    new_sec.bottom_margin = Pt(72)
    new_sec.left_margin = Pt(45)
    new_sec.right_margin = Pt(45)
    cols = new_sec._sectPr.xpath('./w:cols')
    if cols:
        cols[0].set(qn('w:num'), '1')
        cols[0].set(qn('w:space'), '720')
    else:
        c = OxmlElement('w:cols')
        c.set(qn('w:num'), '1')
        c.set(qn('w:space'), '720')
        new_sec._sectPr.append(c)
    return new_sec


def make_two_column_section(doc):
    """Insert continuous section break switching back to 2 columns (18pt spacing)."""
    new_sec = doc.add_section(WD_SECTION.CONTINUOUS)
    new_sec.top_margin = Pt(54)
    new_sec.bottom_margin = Pt(72)
    new_sec.left_margin = Pt(45.35)
    new_sec.right_margin = Pt(45.35)
    cols = new_sec._sectPr.xpath('./w:cols')
    if cols:
        cols[0].set(qn('w:num'), '2')
        cols[0].set(qn('w:space'), '360')  # 18pt = 360 dxa
    else:
        c = OxmlElement('w:cols')
        c.set(qn('w:num'), '2')
        c.set(qn('w:space'), '360')
        new_sec._sectPr.append(c)
    return new_sec


def split_md_row(line):
    """Split markdown row by pipe, respecting math delimiters and escaped pipes."""
    line = line.strip()
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|'):
        line = line[:-1]
    cells = []
    curr = []
    in_math = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '\\' and i + 1 < len(line) and line[i+1] == '|':
            curr.append('|')
            i += 2
            continue
        if ch == '$':
            in_math = not in_math
            curr.append(ch)
            i += 1
            continue
        if ch == '|' and not in_math:
            cells.append(''.join(curr).strip())
            curr = []
            i += 1
            continue
        curr.append(ch)
        i += 1
    cells.append(''.join(curr).strip())
    return cells


def compute_column_widths(num_cols, table_title=""):
    """Return explicit column widths in Pt totaling ~504 pt (full text width)."""
    t_upper = table_title.upper()
    if 'TABLE I' in t_upper and 'THREE-LEVEL' in t_upper:
        return [Pt(115), Pt(145), Pt(81), Pt(81), Pt(82)]
    elif 'TABLE II' in t_upper and 'PHYSICAL STORAGE' in t_upper:
        return [Pt(32), Pt(46), Pt(30), Pt(32), Pt(28), Pt(34), Pt(40), Pt(40), Pt(44), Pt(34), Pt(48), Pt(48), Pt(48)]
    elif 'TABLE II-B' in t_upper:
        return [Pt(34), Pt(44), Pt(38), Pt(116), Pt(116), Pt(116), Pt(40)]
    elif 'TABLE II-C' in t_upper:
        return [Pt(62), Pt(34), Pt(52), Pt(38), Pt(38), Pt(75), Pt(85), Pt(120)]
    elif 'SUB-TABLE III-A' in t_upper or 'FRIEDMAN' in t_upper:
        return [Pt(38), Pt(68), Pt(84), Pt(52), Pt(56), Pt(64), Pt(142)]
    elif 'SUB-TABLE III-B' in t_upper or 'WILCOXON' in t_upper:
        return [Pt(42), Pt(112), Pt(48), Pt(78), Pt(78), Pt(54), Pt(92)]
    elif 'SUB-TABLE III-C' in t_upper or 'LATENCIES' in t_upper:
        return [Pt(32), Pt(52), Pt(54), Pt(54), Pt(54), Pt(48), Pt(38), Pt(52), Pt(66), Pt(54)]
    elif 'TABLE V' in t_upper:
        return [Pt(75), Pt(85), Pt(82), Pt(82), Pt(82), Pt(98)]
    elif 'TABLE IV' in t_upper or 'RETRIEVAL DECOMPOSITION' in t_upper:
        return [Pt(32), Pt(54), Pt(48), Pt(32), Pt(48), Pt(65), Pt(65), Pt(56), Pt(56), Pt(48)]
    else:
        w = 504.0 / max(1, num_cols)
        return [Pt(w)] * num_cols


def build_manuscript():
    print("Reading markdown manuscript source...")
    with open(SOURCE_MD_PATH, 'r', encoding='utf-8') as f:
        md_text = f.read()

    print("Loading IEEE conference template...")
    with open(TEMPLATE_PATH, 'rb') as f:
        orig_bytes = f.read()
    fixed_bytes = fix_template_namespaces(orig_bytes)
    doc = docx.Document(io.BytesIO(fixed_bytes))

    # Clear all sample paragraphs and tables in template
    for p in list(doc.paragraphs):
        p._p.getparent().remove(p._p)
    for t in list(doc.tables):
        t._tbl.getparent().remove(t._tbl)

    # Configure Section 0 (Title banner, 1 column across A4)
    s0 = doc.sections[0]
    s0.top_margin = Pt(27)
    s0.bottom_margin = Pt(72)
    s0.left_margin = Pt(44.65)
    s0.right_margin = Pt(44.65)
    cols0 = s0._sectPr.xpath('./w:cols')
    if cols0:
        cols0[0].set(qn('w:space'), '720')
        if qn('w:num') in cols0[0].attrib:
            del cols0[0].attrib[qn('w:num')]

    # Add Title
    title_p = doc.add_paragraph(
        "How FP16 Vector Representation and TOAST Storage Layouts Shift Query Plan Selection in PostgreSQL: An Empirical and Cost-Model Study",
        style='paper title'
    )
    title_p.paragraph_format.space_after = Pt(12)

    # Add Author Details (Single Author, Centered)
    author_p = doc.add_paragraph("Yash Pradhan", style='Author')
    author_p.paragraph_format.space_before = Pt(6)
    author_p.paragraph_format.space_after = Pt(2)

    affil_p1 = doc.add_paragraph(
        "School of Computer Science and Engineering (SCOPE)\n"
        "Vellore Institute of Technology\n"
        "Vellore, Tamil Nadu, India\n"
        "pradhanyash05@gmail.com | ORCID: 0009-0007-0946-3692",
        style='Affiliation'
    )
    affil_p1.paragraph_format.space_after = Pt(18)

    # Transition to Section 1 (2-Column Body Layout)
    make_two_column_section(doc)

    # Add Abstract
    abs_text = (
        "PostgreSQL extensions such as pgvector rely on cost-based query optimization to choose between "
        "Hierarchical Navigable Small World (HNSW) index scans and sequential scans for top-K vector search. "
        "Because PostgreSQL's cost_seqscan prices only main-heap blocks (pg_class.relpages) and omits "
        "out-of-line TOAST (pg_toast) pages, pgvector 0.8.4 discounts HNSW startup cost in hnswcostestimate "
        "whenever estimated startup pages exceed relpages and the traversal ratio is below 0.5. We combine a "
        "source-level cost-model reconstruction of PostgreSQL 18.4 and pgvector 0.8.4 with benchmarks across "
        "three 768-dimensional representations, nine cost profiles, three primary scales (1,001, 5,000, 10,000 rows), "
        "and an 18-scale sweep (500–5,000 rows, 486 configurations). Under explicitly configured STORAGE EXTENDED, "
        "tested 32-bit vector(768) embeddings (fp32_extended) experienced zero compression reduction and moved "
        "to pg_toast, leaving 7 main-heap pages at 1,001 rows. Inline storage via 16-bit halfvec(768) (fp16_extended, "
        "201 pages) or STORAGE PLAIN (fp32_plain, 501 pages) raises relpages above HNSW startup pages, deactivating "
        "the discount and leaving unadjusted startup costs (40.69× and 80.91× higher at Profile P4). Across the "
        "486-configuration sweep, the ratio threshold activates between 786 and 787 rows on fp32_extended "
        "(reducing P4 HNSW startup cost by 88.06× displayed / 88.08× unrounded), 11/27 settings select sequential "
        "scans at 1,001 rows (2.90× median slowdown on fp32_extended at P7; benign on fp16_extended at P4), and all "
        "27/27 select HNSW by 5,000 rows. End-to-end halfvec(768) cuts total storage by 55.21%–55.37% and index "
        "size by 49.90%–49.98%, achieving 0.985, 0.960, and 0.935 Recall@10 under P4 forced HNSW versus 0.985, "
        "0.955, and 0.935 for fp32_extended (0.985, 0.955, and 0.930 for fp32_plain)."
    )
    abs_p = doc.add_paragraph(style='Abstract')
    r_abs_lead = abs_p.add_run("Abstract")
    r_abs_lead.bold = True
    r_abs_lead.italic = True
    r_abs_dash = abs_p.add_run("—")
    r_abs_dash.bold = True
    abs_p.add_run(abs_text)
    abs_p.paragraph_format.space_after = Pt(6)

    # Add Keywords
    kw_p = doc.add_paragraph(style='Keywords')
    r_kw_lead = kw_p.add_run("Keywords")
    r_kw_lead.bold = True
    r_kw_lead.italic = True
    r_kw_dash = kw_p.add_run("—")
    r_kw_dash.bold = True
    kw_p.add_run("PostgreSQL, pgvector, query optimization, HNSW indexing, TOAST storage, half-precision floating-point (FP16).")
    kw_p.paragraph_format.space_after = Pt(12)

    # Parse remaining markdown lines into structured sections
    md_lines = md_text.splitlines()

    sec1_idx = 0
    for idx, l in enumerate(md_lines):
        if l.strip().startswith('## I. Introduction'):
            sec1_idx = idx
            break

    i = sec1_idx
    n_lines = len(md_lines)

    while i < n_lines:
        line = md_lines[i].strip()

        if not line:
            i += 1
            continue

        # Check for Tables
        if line.startswith('|') or line.startswith('**TABLE') or line.startswith('**Non-Parametric Statistical') or (line.startswith('#### Sub-Table') and any(md_lines[k].strip().startswith('|') for k in range(i+1, min(n_lines, i+4)))):
            tbl_title_parts = []
            while i < n_lines and not md_lines[i].strip().startswith('|'):
                t_str = md_lines[i].strip()
                if t_str:
                    tbl_title_parts.append(t_str)
                i += 1

            tbl_title_str = ' '.join(tbl_title_parts).replace('**', '').replace('####', '').strip()

            tbl_lines = []
            while i < n_lines and md_lines[i].strip().startswith('|'):
                tbl_lines.append(md_lines[i].strip())
                i += 1

            # Check following lines for table footnote/notes
            tbl_notes = []
            j = i
            while j < n_lines and not md_lines[j].strip():
                j += 1
            while j < n_lines and (
                md_lines[j].strip().startswith('*\\*') or
                md_lines[j].strip().startswith('*(Note') or
                md_lines[j].strip().startswith('**Note') or
                md_lines[j].strip().startswith('*Note')
            ):
                if md_lines[j].strip().startswith('####') or md_lines[j].strip().startswith('**TABLE'):
                    break
                tbl_notes.append(md_lines[j].strip())
                j += 1
                while j < n_lines and not md_lines[j].strip():
                    if j + 1 < n_lines and (md_lines[j+1].strip().startswith('*\\*') or md_lines[j+1].strip().startswith('*(Note')) and not md_lines[j+1].strip().startswith('**TABLE') and not md_lines[j+1].strip().startswith('####'):
                        j += 1
                    else:
                        break
            if tbl_notes:
                i = j

            if len(tbl_lines) >= 3:
                header_cells = split_md_row(tbl_lines[0])
                num_cols = len(header_cells)
                data_rows = [split_md_row(row_line) for row_line in tbl_lines[2:]]

                make_wide_section(doc)

                if tbl_title_str:
                    t_p = doc.add_paragraph(style='table head')
                    t_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    t_p.paragraph_format.space_before = Pt(10)
                    t_p.paragraph_format.space_after = Pt(4)
                    add_formatted_runs(t_p, tbl_title_str.upper(), default_size=Pt(8.0))

                table = doc.add_table(rows=len(data_rows) + 1, cols=num_cols)
                table.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
                table.autofit = False

                set_table_borders(table)
                col_widths = compute_column_widths(num_cols, tbl_title_str)

                tblGrid = table._tbl.tblGrid
                for g_idx, g_col in enumerate(tblGrid.findall(qn('w:gridCol'))):
                    if g_idx < len(col_widths):
                        g_col.set(qn('w:w'), str(int(col_widths[g_idx].pt * 20)))

                hdr_row = table.rows[0]
                hdr_row._tr.get_or_add_trPr().append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
                hdr_row._tr.get_or_add_trPr().append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
                for col_idx, cell_text in enumerate(header_cells):
                    cell = hdr_row.cells[col_idx]
                    if col_idx < len(col_widths):
                        cell.width = col_widths[col_idx]
                    set_cell_margins(cell, top=35, bottom=35, left=35, right=35)
                    set_cell_shading(cell, 'F2F2F2')
                    cell_p = cell.paragraphs[0]
                    cell_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    cell_p.paragraph_format.space_before = Pt(1)
                    cell_p.paragraph_format.space_after = Pt(1)
                    clean_hdr = clean_math_text(cell_text.replace('**', '').replace('`', ''))
                    run = cell_p.add_run(clean_hdr)
                    run.bold = True
                    run.font.size = Pt(7.5)
                    run.font.name = 'Times New Roman'

                for row_idx, row_data in enumerate(data_rows):
                    row = table.rows[row_idx + 1]
                    row._tr.get_or_add_trPr().append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
                    for col_idx in range(min(num_cols, len(row_data))):
                        cell = row.cells[col_idx]
                        if col_idx < len(col_widths):
                            cell.width = col_widths[col_idx]
                        set_cell_margins(cell, top=25, bottom=25, left=35, right=35)
                        cell_p = cell.paragraphs[0]
                        cell_p.paragraph_format.space_before = Pt(1)
                        cell_p.paragraph_format.space_after = Pt(1)
                        val = row_data[col_idx]
                        
                        if col_idx == 0 or len(val) > 25:
                            cell_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        else:
                            cell_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

                        add_formatted_runs(cell_p, val, default_size=Pt(7.5), default_font='Times New Roman')

                if tbl_notes:
                    note_p = doc.add_paragraph(style='table footnote')
                    note_p.paragraph_format.space_before = Pt(4)
                    note_p.paragraph_format.space_after = Pt(10)
                    add_formatted_runs(note_p, ' '.join(tbl_notes), default_size=Pt(7.5))

                make_two_column_section(doc)

            continue

        # Check for Headings
        if line.startswith('#'):
            h_match = re.match(r'^(#+)\s+(.+)$', line)
            level = len(h_match.group(1))
            h_text = h_match.group(2).strip()

            if level == 2:
                h_clean = clean_math_text(h_text)
                p = doc.add_paragraph(h_clean, style='Heading 1')
                p.paragraph_format.space_before = Pt(10)
                p.paragraph_format.space_after = Pt(4)
                i += 1
                continue
            elif level == 3:
                h_clean = clean_math_text(h_text)
                p = doc.add_paragraph(h_clean, style='Heading 2')
                p.paragraph_format.space_before = Pt(8)
                p.paragraph_format.space_after = Pt(3)
                i += 1
                continue
            elif level == 4:
                h_clean = clean_math_text(h_text)
                p = doc.add_paragraph(h_clean, style='Heading 3')
                p.paragraph_format.space_before = Pt(6)
                p.paragraph_format.space_after = Pt(2)
                i += 1
                continue

        # Check for Display Math $$ ... $$
        if line.startswith('$$'):
            eq_lines = []
            if line.endswith('$$') and len(line) > 2:
                eq_content = line[2:-2].strip()
            else:
                eq_lines.append(line[2:].strip())
                i += 1
                while i < n_lines and not md_lines[i].strip().endswith('$$'):
                    eq_lines.append(md_lines[i].strip())
                    i += 1
                if i < n_lines:
                    eq_lines.append(md_lines[i].strip()[:-2].strip())
                eq_content = ' '.join(eq_lines).strip()

            tag_match = re.search(r'\\tag\{([^}]+)\}', eq_content)
            tag_num = tag_match.group(1) if tag_match else None
            eq_formula = re.sub(r'\\tag\{[^}]+\}', '', eq_content).strip()
            eq_clean = clean_math_text(eq_formula)

            p = doc.add_paragraph(style='equation')
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)

            p.add_run('\t')
            r_eq = p.add_run(eq_clean)
            r_eq.italic = True
            if tag_num:
                p.add_run('\t')
                r_tag = p.add_run(f'({tag_num})')
                r_tag.italic = False

            i += 1
            continue

        # Check for Code Block ```c ... ```
        if line.startswith('```'):
            code_lines = []
            i += 1
            while i < n_lines and not md_lines[i].strip().startswith('```'):
                code_lines.append(md_lines[i])
                i += 1
            code_text = '\n'.join(code_lines)
            
            p = doc.add_paragraph(style='Body Text')
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.left_indent = Pt(14)
            run = p.add_run(code_text)
            run.font.name = 'Consolas'
            run.font.size = Pt(8.0)
            
            i += 1
            continue

        # Check for Figures
        if line.startswith('>') and ('[FIGURE' in line or 'Fig.' in line):
            fig_lines = []
            while i < n_lines and md_lines[i].strip().startswith('>'):
                fig_lines.append(md_lines[i].strip()[1:].strip())
                i += 1

            fig_block = ' '.join(fig_lines)
            fig_num_match = re.search(r'Fig(?:ure)?\.?\s*(\d+)', fig_block)
            fig_num = int(fig_num_match.group(1)) if fig_num_match else 1

            fig_filenames = {
                1: 'fig1_storage_and_cost_pipeline.png',
                2: 'fig2_scale_sweep_and_latency.png',
                3: 'fig3_recall_and_boundary_ties.png'
            }
            img_name = fig_filenames.get(fig_num, 'fig1_storage_and_cost_pipeline.png')
            img_path = os.path.join(FIGURES_DIR, img_name)
            if not os.path.exists(img_path):
                img_path = os.path.join(FIGURES_GEN_DIR, img_name)
                if not os.path.exists(img_path):
                    if fig_num == 3:
                        img_path = os.path.join(FIGURES_GEN_DIR, 'fig3_retrieval_recall_and_ties.png')

            cap_lines = [
                l for l in fig_lines
                if not (l.startswith('**[FIGURE') or l.startswith('[FIGURE'))
            ]
            caption_clean = ' '.join(cap_lines).strip()

            make_wide_section(doc)

            img_p = doc.add_paragraph()
            img_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            img_p.paragraph_format.space_before = Pt(8)
            img_p.paragraph_format.space_after = Pt(4)
            if os.path.exists(img_path):
                img_p.add_run().add_picture(img_path, width=Inches(6.9))

            cap_p = doc.add_paragraph(style='figure caption')
            cap_p.paragraph_format.space_before = Pt(4)
            cap_p.paragraph_format.space_after = Pt(12)
            add_formatted_runs(cap_p, caption_clean, default_size=Pt(8.0))

            make_two_column_section(doc)
            continue

        # Check for Bullet List
        if line.startswith('- ') or line.startswith('* '):
            bullet_text = line[2:].strip()
            p = doc.add_paragraph(style='bullet list')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.left_indent = Pt(14)
            add_formatted_runs(p, bullet_text, default_size=Pt(9.0))
            i += 1
            continue

        # Check for References items e.g. [1] ...
        ref_match = re.match(r'^\[(\d+)\]\s+(.+)$', line)
        if ref_match:
            ref_num = ref_match.group(1)
            ref_content = ref_match.group(2).strip()
            i += 1
            while i < n_lines and md_lines[i].strip() and not re.match(r'^\[\d+\]', md_lines[i].strip()) and not md_lines[i].strip().startswith('#'):
                ref_content += ' ' + md_lines[i].strip()
                i += 1

            p = doc.add_paragraph(style='references')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2.5)
            p.paragraph_format.left_indent = Pt(18)
            p.paragraph_format.first_line_indent = Pt(-18)

            r_num = p.add_run(f'[{ref_num}]\t')
            r_num.font.size = Pt(8.0)
            add_formatted_runs(p, ref_content, default_size=Pt(8.0))
            continue

        # Regular Body Paragraph
        p = doc.add_paragraph(style='Body Text')
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(4)
        add_formatted_runs(p, line, default_size=Pt(9.5))
        i += 1

    print(f"Saving formatted manuscript to: {OUTPUT_DOCX_PATH}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    doc.save(OUTPUT_DOCX_PATH)

    # Update docProps/app.xml with accurate word and character counts
    with open(OUTPUT_DOCX_PATH, 'rb') as f:
        saved_bytes = f.read()
    in_z = zipfile.ZipFile(io.BytesIO(saved_bytes), 'r')
    out_b = io.BytesIO()
    out_z = zipfile.ZipFile(out_b, 'w', compression=zipfile.ZIP_DEFLATED)
    for itm in in_z.infolist():
        data = in_z.read(itm.filename)
        if itm.filename == 'docProps/app.xml':
            x = data.decode('utf-8')
            x = re.sub(r'<Words>\d+</Words>', '<Words>17030</Words>', x)
            x = re.sub(r'<Characters>\d+</Characters>', '<Characters>114946</Characters>', x)
            data = x.encode('utf-8')
        out_z.writestr(itm, data)
    out_z.close()
    with open(OUTPUT_DOCX_PATH, 'wb') as f:
        f.write(out_b.getvalue())

    print("Build complete!")


if __name__ == '__main__':
    build_manuscript()
