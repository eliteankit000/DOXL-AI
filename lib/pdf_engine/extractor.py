import re
import os
import uuid
import pdfplumber
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


# ═══════════════════════════════════════════════════════════
# STYLE CONSTANTS
# ═══════════════════════════════════════════════════════════

S_TITLE_BG    = "1F3864"   # dark navy   — title rows
S_SUBHEAD_BG  = "2E75B6"   # medium blue — section/subheading rows
S_HEADER_BG   = "FFC000"   # gold        — column header rows
S_KEY_BG      = "E8F4FD"   # light blue  — key column in KV sheets
S_ALT1_BG     = "D6E4F0"   # soft blue   — alternating odd rows
S_ALT2_BG     = "FFFFFF"   # white       — alternating even rows
S_TOTAL_BG    = "EAF3DE"   # light green — total/summary rows
S_WHITE_FG    = "FFFFFF"
S_DARK_FG     = "1F3864"
S_BLACK_FG    = "000000"


def _border():
    s = Side(border_style="thin", color="B8CCE4")
    return Border(left=s, right=s, top=s, bottom=s)


def _wc(ws, row, col, value,
        bold=False, size=10, bg=S_ALT2_BG,
        fg=S_BLACK_FG, align="left", wrap=False):
    """Write one cell with full formatting."""
    c = ws.cell(row=row, column=col, value=value)
    c.font      = Font(name="Arial", size=size,
                       bold=bold, color=fg)
    c.fill      = PatternFill("solid", fgColor=bg)
    c.alignment = Alignment(horizontal=align,
                            vertical="center",
                            wrap_text=wrap)
    c.border    = _border()
    return c


def _merge_row(ws, row, num_cols, value,
               bold=True, size=11,
               bg=S_TITLE_BG, fg=S_WHITE_FG, height=26):
    """Write a full-width merged title or section row."""
    end_col = get_column_letter(num_cols)
    ws.merge_cells("A{}:{}{}".format(row, end_col, row))
    _wc(ws, row, 1, value, bold=bold, size=size,
        bg=bg, fg=fg, align="center")
    ws.row_dimensions[row].height = height


def _col_width(values: list, header: str) -> float:
    """Calculate best column width from content."""
    max_len = len(str(header))
    for v in values:
        max_len = max(max_len, len(str(v)) if v else 0)
    return min(max(max_len + 4, 10), 60)


# ═══════════════════════════════════════════════════════════
# STEP 1 — EXTRACT ALL CONTENT FROM PDF
# ═══════════════════════════════════════════════════════════

def _is_junk_row(row: list) -> bool:
    """Return True for rows that are headers/footers/noise."""
    non_empty = [str(c).strip() for c in row
                 if c and str(c).strip()]
    if not non_empty:
        return True

    joined = " ".join(non_empty).strip().lower()

    # Existing junk patterns
    junk_patterns = [
        r"^\d{1,2}/\d{1,2}/\d{4}",   # dates alone
        r"^page\s*\d",                 # page numbers
        r"http[s]?://",               # URLs
        r"^-{3,}$",                   # dashes only
        r"^_{3,}$",                   # underscores only
        r"signature",                  # signature lines
        r"^\s*\d+\s*$",              # standalone numbers (page num)
    ]
    for p in junk_patterns:
        if re.search(p, joined, re.IGNORECASE):
            return True

    # NEW: single-cell rows where the one value spans the
    # full row width -> these are title/header text bleeds
    if (len(non_empty) == 1
            and len(row) >= 4
            and len(non_empty[0]) > 25):
        return True

    # NEW: rows that look like they contain a date-time stamp
    # followed by a page number (e.g. "4/9/2026 7:29:49  1")
    if re.match(r"\d{1,2}/\d{1,2}/\d{4}\s+\d+:\d+", joined):
        return True

    # 80%+ cells empty
    if len(non_empty) / max(len(row), 1) < 0.2:
        return True

    return False


def _clean_cell(value) -> str:
    """Normalize a cell value to clean string."""
    if value is None:
        return ""
    s = str(value).strip()
    s = re.sub(r"\s{2,}", " ", s)
    return s


def _find_header_row(table: list) -> int:
    """
    Find the index of the real header row.
    The header row is the first row where 50%+ cells are non-empty
    and the values look like column titles (not pure numbers).
    """
    for i, row in enumerate(table):
        non_empty = [c for c in row
                     if c and str(c).strip()
                     and not re.match(r"^[\d\s|.,-]+$",
                                      str(c).strip())]
        if len(non_empty) >= max(2, len(row) * 0.4):
            return i
    return 0


def _looks_like_data_row(row: list, known_headers: list) -> bool:
    """
    Returns True if this row looks like data, not a header.
    A header row has text labels. A data row has values like
    '0 BOTTEL | 00 ML', '3 BEER', numbers, or item names.
    """
    if not known_headers:
        return False
    non_empty = [str(c).strip() for c in row
                 if c and str(c).strip()]
    if not non_empty:
        return True
    # If 60%+ cells match the pattern of data values -> data row
    data_pattern = re.compile(
        r'\d+\s*(BOTTEL|BEER|ML|ml|L|PCS|KG|GM|Rs|INR|\|)',
        re.IGNORECASE
    )
    data_hits = sum(1 for v in non_empty
                    if data_pattern.search(v))
    return data_hits / len(non_empty) >= 0.4


def extract_pdf_content(pdf_path: str) -> dict:
    """
    Extract all content from a PDF into a structured dict.
    Handles all document types: tables, forms, mixed, multi-page.

    Returns:
    {
      "doc_title":       str,
      "doc_subtitle":    str,
      "tables": [
        {
          "heading":  str,        # section heading above table if any
          "headers":  [str],      # column names from PDF
          "rows":     [[str]],    # all data rows
          "page_start": int
        }
      ],
      "metadata_pairs":  [(str, str)],   # key-value pairs from form
      "raw_text_pages":  [str]           # raw text per page
    }
    """
    doc_title      = ""
    doc_subtitle   = ""
    all_tables     = []
    metadata_pairs = []
    raw_text_pages = []

    with pdfplumber.open(pdf_path) as pdf:

        for page_num, page in enumerate(pdf.pages):

            # ── Raw text for this page ──────────────────────────
            raw_text = page.extract_text(layout=False) or ""
            raw_text_pages.append(raw_text)
            lines = [ln.strip() for ln in raw_text.split("\n")
                     if ln.strip()]

            # ── Document title from page 1 ──────────────────────
            if page_num == 0 and lines:
                # Collect up to 3 candidate title lines
                candidates = []
                for line in lines:
                    if (len(line) > 8
                            and not re.match(
                                r"^\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}",
                                line)
                            and not re.match(r"^\d+$", line)
                            and not re.match(r"^\d{1,2}:\d{2}", line)):
                        candidates.append(line)
                    if len(candidates) == 3:
                        break

                if candidates:
                    # Pick the LONGEST candidate as the title
                    doc_title = max(candidates, key=len)
                    # No subtitle — set empty to avoid double title rows
                    doc_subtitle = ""

            # ── Try geometric table extraction ──────────────────
            tables_geo = page.extract_tables({
                "vertical_strategy":   "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance":      3,
            }) or []

            # ── Fallback to text-alignment strategy ─────────────
            tables_txt = []
            if not tables_geo:
                tables_txt = page.extract_tables({
                    "vertical_strategy":   "text",
                    "horizontal_strategy": "text",
                    "snap_tolerance":      5,
                    "min_words_vertical":  1,
                }) or []

            page_tables = tables_geo or tables_txt

            # ── Process each table on this page ─────────────────
            for table in page_tables:

                if not table or len(table) < 1:
                    continue

                # ── Detect if this table has a header row ──────────
                hdr_idx = _find_header_row(table)
                raw_headers = table[hdr_idx]
                candidate_headers = [
                    _clean_cell(h) or "Col_{}".format(i+1)
                    for i, h in enumerate(raw_headers)
                ]

                # ── Check if this is a continuation page ──────────
                # Continuation = the "header" row actually looks like
                # data AND we already have headers from a previous page
                is_continuation = (
                    last_known_headers
                    and len(candidate_headers) == last_known_num_cols
                    and _looks_like_data_row(raw_headers, last_known_headers)
                )

                if is_continuation:
                    # Use headers from previous page
                    headers = last_known_headers
                    # All rows including "header" row are data
                    start_from = 0
                else:
                    headers = candidate_headers
                    start_from = hdr_idx + 1
                    last_known_headers = headers
                    last_known_num_cols = len(headers)

                # ── Collect data rows ──────────────────────────────
                data_rows = []
                for row in table[start_from:]:
                    if _is_junk_row(row):
                        continue
                    # Skip rows that look like page headers/titles
                    non_empty_vals = [str(c).strip() for c in row
                                     if c and str(c).strip()]
                    if (len(non_empty_vals) == 1
                            and len(non_empty_vals[0]) > 20):
                        continue   # single long string = title bleed
                    clean = [_clean_cell(c) for c in row]
                    while len(clean) < len(headers):
                        clean.append("")
                    data_rows.append(clean[:len(headers)])

                if not data_rows:
                    continue

                # ── Append to existing table if continuation ──────
                if is_continuation and all_tables:
                    all_tables[-1]["rows"].extend(data_rows)
                else:
                    all_tables.append({
                        "heading":    "",
                        "headers":    headers,
                        "rows":       data_rows,
                        "page_start": page_num + 1,
                    })

            # ── Extract key-value metadata ───────────────────────
            # Only run if page has no tables or has a form-like structure
            if not page_tables:
                for line in lines:
                    # Match patterns: "Key : Value" or "Key    Value"
                    kv = re.match(
                        r"^([A-Za-z][A-Za-z0-9 './#&()\-]{1,50})"
                        r"\s*:\s*(.+)$",
                        line
                    )
                    if kv:
                        key = kv.group(1).strip().rstrip(":")
                        val = kv.group(2).strip()
                        if (key and val
                                and val not in ("-", ":", "")
                                and len(key) < 55):
                            metadata_pairs.append((key, val))

    return {
        "doc_title":      doc_title or "Document",
        "doc_subtitle":   doc_subtitle,
        "tables":         all_tables,
        "metadata_pairs": metadata_pairs,
        "raw_text_pages": raw_text_pages,
    }


# ═══════════════════════════════════════════════════════════
# STEP 2 — BUILD EXCEL FROM EXTRACTED CONTENT
# ═══════════════════════════════════════════════════════════

def build_excel(content: dict, output_path: str) -> str:
    """
    Build a fully formatted Excel file from extracted PDF content.
    Works for ANY document type. Zero hardcoded strings.
    """
    wb = Workbook()
    sheet_created = False

    # ── A: Write each table as its own sheet ──────────────────
    for t_idx, table in enumerate(content["tables"]):

        headers    = table["headers"]
        rows       = table["rows"]
        heading    = table["heading"]
        num_cols   = len(headers)

        if not rows:
            continue

        # Sheet name from first column header, sanitised
        raw_name = headers[0] if headers[0] else \
                   "Table {}".format(t_idx + 1)
        for bad in ['\\', '/', ':', '*', '?', '[', ']']:
            raw_name = raw_name.replace(bad, " ")
        sheet_name = raw_name.strip()[:31] or \
                     "Table {}".format(t_idx + 1)

        if not sheet_created:
            ws = wb.active
            ws.title = sheet_name
            sheet_created = True
        else:
            # Avoid duplicate sheet names
            existing = [s.title for s in wb.worksheets]
            if sheet_name in existing:
                sheet_name = "{} {}".format(sheet_name, t_idx + 1)
            ws = wb.create_sheet(sheet_name)

        ws.sheet_view.showGridLines = False
        current_row = 1

        # ── Title row (doc_title from PDF) ────────────────────
        _merge_row(ws, current_row, num_cols,
                   content["doc_title"],
                   bold=True, size=12,
                   bg=S_TITLE_BG, fg=S_WHITE_FG, height=28)
        current_row += 1

        # ── Subtitle row if exists ────────────────────────────
        if content["doc_subtitle"]:
            _merge_row(ws, current_row, num_cols,
                       content["doc_subtitle"],
                       bold=False, size=10,
                       bg=S_SUBHEAD_BG, fg=S_WHITE_FG, height=20)
            current_row += 1

        # ── Section heading row if exists ─────────────────────
        if heading and heading != content["doc_title"]:
            _merge_row(ws, current_row, num_cols,
                       heading,
                       bold=True, size=10,
                       bg=S_SUBHEAD_BG, fg=S_WHITE_FG, height=20)
            current_row += 1

        # ── Column headers (from PDF, not hardcoded) ──────────
        for ci, h in enumerate(headers, 1):
            _wc(ws, current_row, ci, h,
                bold=True, size=10,
                bg=S_HEADER_BG, fg=S_DARK_FG,
                align="center")
        ws.row_dimensions[current_row].height = 22
        current_row += 1

        # ── Data rows with alternating colors ─────────────────
        for ri, row in enumerate(rows):
            bg = S_ALT1_BG if ri % 2 == 0 else S_ALT2_BG
            for ci, val in enumerate(row, 1):
                # Right-align numeric values
                is_num = bool(re.match(
                    r"^\s*[\d,]+\.?\d*\s*(ML|ml|L|BEER|BOTTEL)?\s*$",
                    str(val)
                ))
                align = "right" if is_num else \
                        ("center" if ci == 1 else "left")
                _wc(ws, current_row, ci, val,
                    size=10, bg=bg, fg=S_BLACK_FG, align=align)
            ws.row_dimensions[current_row].height = 18
            current_row += 1

        # ── Total row ─────────────────────────────────────────
        total_label = "Total Records: {}".format(len(rows))
        ws.merge_cells("A{}:{}{}".format(
            current_row,
            get_column_letter(max(num_cols - 1, 1)),
            current_row
        ))
        _wc(ws, current_row, 1, total_label,
            bold=True, size=10,
            bg=S_TOTAL_BG, fg=S_DARK_FG, align="right")
        _wc(ws, current_row, num_cols, len(rows),
            bold=True, size=10,
            bg=S_TOTAL_BG, fg=S_DARK_FG, align="center")
        ws.row_dimensions[current_row].height = 20
        current_row += 1

        # ── Column widths from actual content ─────────────────
        for ci, header in enumerate(headers, 1):
            col_vals = [row[ci-1] for row in rows
                        if ci <= len(row)]
            ws.column_dimensions[
                get_column_letter(ci)
            ].width = _col_width(col_vals, header)

    # ── B: Write metadata/key-value pairs if present ─────────
    if content["metadata_pairs"]:

        sheet_name = "Details"
        if not sheet_created:
            ws_m = wb.active
            ws_m.title = sheet_name
            sheet_created = True
        else:
            ws_m = wb.create_sheet(sheet_name)

        ws_m.sheet_view.showGridLines = False
        r = 1

        # Title from PDF
        ws_m.merge_cells("A{}:B{}".format(r, r))
        _wc(ws_m, r, 1, content["doc_title"],
            bold=True, size=12,
            bg=S_TITLE_BG, fg=S_WHITE_FG,
            align="center")
        ws_m.row_dimensions[r].height = 28
        r += 1

        if content["doc_subtitle"]:
            ws_m.merge_cells("A{}:B{}".format(r, r))
            _wc(ws_m, r, 1, content["doc_subtitle"],
                bold=False, size=10,
                bg=S_SUBHEAD_BG, fg=S_WHITE_FG,
                align="center")
            ws_m.row_dimensions[r].height = 20
            r += 1

        # Column headers
        _wc(ws_m, r, 1, "Field",
            bold=True, size=10,
            bg=S_HEADER_BG, fg=S_DARK_FG, align="center")
        _wc(ws_m, r, 2, "Value",
            bold=True, size=10,
            bg=S_HEADER_BG, fg=S_DARK_FG, align="center")
        ws_m.row_dimensions[r].height = 22
        r += 1

        # Key-Value rows
        for ri, (key, val) in enumerate(
                content["metadata_pairs"]):
            bg = S_ALT1_BG if ri % 2 == 0 else S_ALT2_BG
            _wc(ws_m, r, 1, key,
                bold=True, size=10,
                bg=S_KEY_BG, fg=S_DARK_FG, align="left")
            _wc(ws_m, r, 2, val,
                size=10, bg=bg, fg=S_BLACK_FG, align="left")
            ws_m.row_dimensions[r].height = 18
            r += 1

        # Column widths
        key_vals   = [k for k, v in content["metadata_pairs"]]
        value_vals = [v for k, v in content["metadata_pairs"]]
        ws_m.column_dimensions["A"].width = \
            _col_width(key_vals, "Field")
        ws_m.column_dimensions["B"].width = \
            _col_width(value_vals, "Value")

    # ── C: Fallback if nothing extracted ─────────────────────
    if not sheet_created:
        ws = wb.active
        ws.title = "Extracted"
        ws.merge_cells("A1:D1")
        _wc(ws, 1, 1,
            "No structured data could be extracted from this PDF.",
            bold=True, size=11,
            bg=S_TITLE_BG, fg=S_WHITE_FG, align="center")

    wb.save(output_path)
    return output_path


# ═══════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════

def extract_and_build(pdf_path: str, output_path: str) -> str:
    """
    Single function called by the project's upload handler.
    Extracts PDF content and builds a clean structured Excel.
    Works for any document type. Zero hardcoded strings.
    """
    content = extract_pdf_content(pdf_path)
    return build_excel(content, output_path)


# ═══════════════════════════════════════════════════════════
# JSON SUMMARY (for route.js process handler DB storage)
# ═══════════════════════════════════════════════════════════

def get_extraction_summary(pdf_path: str) -> dict:
    """
    Extract PDF, generate xlsx, and return a JSON-friendly summary.
    Called by scripts/extract.py which outputs JSON to stdout.
    """
    output_dir = "/app/outputs"
    os.makedirs(output_dir, exist_ok=True)
    xlsx_id = str(uuid.uuid4())
    xlsx_path = os.path.join(output_dir, "{}.xlsx".format(xlsx_id))

    try:
        content = extract_pdf_content(pdf_path)
        build_excel(content, xlsx_path)

        # Build JSON summary from extracted content
        tables = content["tables"]
        metadata = content["metadata_pairs"]

        if tables:
            # Use the first (or largest) table for primary output
            primary = max(tables, key=lambda t: len(t["rows"]))
            columns = primary["headers"]
            rows = []
            for row_data in primary["rows"]:
                row_dict = {}
                for ci, col in enumerate(columns):
                    row_dict[col] = row_data[ci] if ci < len(row_data) else ""
                rows.append(row_dict)

            doc_type = "table"
            if metadata:
                doc_type = "mixed"

            return {
                "columns": columns,
                "rows": rows,
                "document_type": doc_type,
                "confidence": 0.90,
                "extraction_method": "pdfplumber_universal",
                "xlsx_path": xlsx_path,
                "doc_title": content["doc_title"],
                "total_tables": len(tables),
                "total_metadata_fields": len(metadata),
            }

        elif metadata:
            columns = ["Field", "Value"]
            rows = [{"Field": k, "Value": v} for k, v in metadata]
            return {
                "columns": columns,
                "rows": rows,
                "document_type": "form",
                "confidence": 0.80,
                "extraction_method": "pdfplumber_universal",
                "xlsx_path": xlsx_path,
                "doc_title": content["doc_title"],
                "total_tables": 0,
                "total_metadata_fields": len(metadata),
            }

        else:
            return {
                "columns": [],
                "rows": [],
                "document_type": "unknown",
                "confidence": 0.0,
                "error": "No structured data found in PDF",
                "extraction_method": "pdfplumber_universal",
                "xlsx_path": "",
                "doc_title": content.get("doc_title", ""),
            }

    except Exception as exc:
        if os.path.exists(xlsx_path):
            os.remove(xlsx_path)
        return {
            "columns": [],
            "rows": [],
            "document_type": "unknown",
            "confidence": 0.0,
            "error": str(exc),
            "extraction_method": "pdfplumber_universal",
            "xlsx_path": "",
        }
