"""
DocXL AI — PDF-to-Excel Extractor

Uses ONLY pdfplumber with lines/lines strategy.
Parses metadata blob with regex.
Writes styled Excel with openpyxl.

NO pandas. NO camelot. NO tabula. NO confidence scores.
"""
import pdfplumber
import re
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


def _border():
    s = Side(border_style='thin', color='B8CCE4')
    return Border(left=s, right=s, top=s, bottom=s)


def _wcell(ws, row, col, value, bold=False, size=10,
           bg='FFFFFF', fg='000000', halign='left'):
    c = ws.cell(row=row, column=col, value=value)
    c.font = Font(name='Arial', size=size, bold=bold, color=fg)
    c.fill = PatternFill('solid', fgColor=bg)
    c.alignment = Alignment(horizontal=halign, vertical='center', wrap_text=True)
    c.border = _border()
    return c


def _is_skip_row(row):
    """Return True if this row should be skipped (empty, dashes, URLs, signature)."""
    if not row:
        return True
    texts = [str(v).strip() if v else '' for v in row]
    joined = ' '.join(texts).strip()
    if not joined:
        return True
    if all(c in '-— ' for c in joined):
        return True
    if 'http' in joined.lower():
        return True
    if 'signature' in joined.lower():
        return True
    return False


def _get_field(pattern, text):
    """Extract a regex group from text, return '-' if not found."""
    m = re.search(pattern, text)
    v = m.group(1).strip() if m else '-'
    return v if v not in (':', '', ' ') else '-'


def extract_and_build(pdf_path: str, output_path: str) -> str:
    """
    Extract tables + metadata from PDF and build a styled .xlsx file.

    Uses pdfplumber with lines/lines strategy.
    Parses metadata blob with regex.
    Writes exactly 2 sheets: 'Form Details' and 'Subject Details'.

    Returns output_path on success.
    """

    # ── EXTRACT ──────────────────────────────────────────────
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        all_tables = page.extract_tables({
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines"
        })

        if not all_tables or len(all_tables) == 0:
            raise ValueError("No tables found in PDF")

        rows = all_tables[0]

    if not rows or len(rows) < 3:
        raise ValueError("PDF table has fewer than 3 rows")

    # ── PARSE METADATA ───────────────────────────────────────
    blob = re.sub(r'\n', ' ', rows[1][0] or '') if len(rows) > 1 and rows[1] and rows[1][0] else ''

    meta = [
        ("Institute Name",  _get_field(r'Institute Name\s*:\s*(.+?)(?=Semester\s*:)', blob)),
        ("Semester",        _get_field(r'Semester\s*:\s*:?\s*(.+?)(?=Enrollment No)', blob)),
        ("Enrollment No",   _get_field(r'Enrollment No\s*:\s*(\S+)', blob)),
        ("Student Name",    _get_field(r"Student's Name\s*:\s*:?\s*(\S+)", blob)),
        ("Mobile No",       _get_field(r'Mobile No\s*:\s*(\d+)\s+EmailID', blob)),
        ("Email ID",        _get_field(r'EmailID\s*:\s*(\S+)', blob)),
        ("Date of Filling", _get_field(r'Date Of Filling\s*:\s*(\S+)', blob)),
        ("Father Name",     _get_field(r"Father's Name\s*:\s*(\S+)\s+Occupation", blob)),
        ("Annual Income",   _get_field(r'Annual Income\s*:\s*([\d.]+)', blob)),
        ("Father Mobile",   _get_field(r'Mobile No\s*:\s*(\d+)\s+Office Phone', blob)),
        ("Due Amount",      _get_field(r'Due Amount\s*:\s*([\d.]+)', blob)),
        ("Paid Amount",     _get_field(r'Paid Amount\s*:\s*(-|[\d.]+)', blob)),
        ("Committed Date",  _get_field(r'Comitted Date\s*:\s*(\S+)', blob)),
        ("Transaction ID",  _get_field(r'TransactionID\s*:\s*(-|\w+)', blob)),
        ("Bank Ref. No.",   _get_field(r'Bank Ref\. No\.\s*:\s*(-|\w+)', blob)),
    ]
    md = dict(meta)

    # ── FIND TABLE HEADER AND DATA ROWS ─────────────────────
    header_idx = None
    for i, r in enumerate(rows):
        if r and len(r) >= 2:
            cell0 = str(r[0] or '').strip().lower()
            if cell0 in ('sr.', 'sr', 'sno', 's.no', 'no.', '#', 'sl.'):
                header_idx = i
                break

    if header_idx is None:
        # Fallback: assume row 2 is header (as per the known format)
        header_idx = 2

    # Collect data rows after header, skip footer rows
    subjects = []
    for r in rows[header_idx + 1:]:
        if _is_skip_row(r):
            continue
        # Take only first 3 columns (Sr., Subject Code, Subject Name)
        num_cols = min(len(r), 3)
        row_data = [str(v).strip() if v else '' for v in r[:num_cols]]
        if any(row_data):
            subjects.append(row_data)

    # Ensure each row has exactly 3 columns
    for i in range(len(subjects)):
        while len(subjects[i]) < 3:
            subjects[i].append('')

    # Get header labels
    header_row = rows[header_idx] if header_idx < len(rows) else ['Sr.', 'Subject Code', 'Subject Name']
    header_labels = [str(v).strip() if v else '' for v in header_row[:3]]
    while len(header_labels) < 3:
        header_labels.append('')
    if not header_labels[0]:
        header_labels[0] = 'Sr.'
    if not header_labels[1]:
        header_labels[1] = 'Subject Code'
    if not header_labels[2]:
        header_labels[2] = 'Subject Name'

    # ── BUILD WORKBOOK ───────────────────────────────────────
    wb = Workbook()

    # ── Sheet 1: Form Details ────────────────────────────────
    ws1 = wb.active
    ws1.title = 'Form Details'
    ws1.sheet_view.showGridLines = False

    # Title row
    ws1.merge_cells('A1:B1')
    _wcell(ws1, 1, 1, 'SAGE UNIVERSITY \u2014 SEMESTER REGISTRATION FORM',
           bold=True, size=12, bg='1F3864', fg='FFFFFF', halign='center')
    _wcell(ws1, 1, 2, None, bg='1F3864')
    ws1.row_dimensions[1].height = 28

    # Info row
    ws1.merge_cells('A2:B2')
    _wcell(ws1, 2, 1, '{}  |  {}  |  {}'.format(
        md['Student Name'], md['Enrollment No'], md['Semester']),
        bold=True, size=9, bg='2E75B6', fg='FFFFFF', halign='center')
    _wcell(ws1, 2, 2, None, bg='2E75B6')
    ws1.row_dimensions[2].height = 18

    # Sections
    sections = [
        ('Personal Information',
         ['Institute Name', 'Semester', 'Enrollment No',
          'Student Name', 'Mobile No', 'Email ID', 'Date of Filling']),
        ("Father's Information",
         ['Father Name', 'Annual Income', 'Father Mobile']),
        ('Paid Fees Details',
         ['Due Amount', 'Paid Amount', 'Committed Date',
          'Transaction ID', 'Bank Ref. No.']),
    ]

    r = 3
    for title, fields in sections:
        ws1.merge_cells('A{}:B{}'.format(r, r))
        _wcell(ws1, r, 1, '  ' + title, bold=True, size=10,
               bg='2E75B6', fg='FFFFFF')
        _wcell(ws1, r, 2, None, bg='2E75B6')
        ws1.row_dimensions[r].height = 20
        r += 1
        for f in fields:
            _wcell(ws1, r, 1, f, bold=True, size=10, bg='E8F4FD', fg='1F3864')
            _wcell(ws1, r, 2, md.get(f, '-'), size=10, bg='FFFFFF', fg='000000')
            ws1.row_dimensions[r].height = 18
            r += 1
        # blank gap row
        r += 1

    ws1.column_dimensions['A'].width = 22
    ws1.column_dimensions['B'].width = 40

    # ── Sheet 2: Subject Details ─────────────────────────────
    ws2 = wb.create_sheet('Subject Details')
    ws2.sheet_view.showGridLines = False

    # Title row
    ws2.merge_cells('A1:C1')
    _wcell(ws2, 1, 1, 'Subject Enrollment \u2014 {}'.format(md['Semester']),
           bold=True, size=12, bg='1F3864', fg='FFFFFF', halign='center')
    _wcell(ws2, 1, 2, None, bg='1F3864')
    _wcell(ws2, 1, 3, None, bg='1F3864')
    ws2.row_dimensions[1].height = 28

    # Info row
    ws2.merge_cells('A2:C2')
    _wcell(ws2, 2, 1, 'Student: {}  |  Enrollment: {}  |  Date: {}'.format(
        md['Student Name'], md['Enrollment No'], md['Date of Filling']),
        bold=True, size=9, bg='2E75B6', fg='FFFFFF', halign='center')
    _wcell(ws2, 2, 2, None, bg='2E75B6')
    _wcell(ws2, 2, 3, None, bg='2E75B6')
    ws2.row_dimensions[2].height = 18

    # Blank spacer
    ws2.row_dimensions[3].height = 6

    # Header row (row 4)
    for ci, h in enumerate(header_labels, 1):
        c = ws2.cell(row=4, column=ci, value=h)
        c.font = Font(name='Arial', size=10, bold=True, color='1F3864')
        c.fill = PatternFill('solid', fgColor='FFC000')
        c.alignment = Alignment(horizontal='center', vertical='center')
        c.border = _border()
    ws2.row_dimensions[4].height = 22

    # Data rows
    for ri, subj in enumerate(subjects, 5):
        row_bg = 'D6E4F0' if ri % 2 == 1 else 'FFFFFF'
        for ci, val in enumerate(subj, 1):
            _wcell(ws2, ri, ci, val, size=10, bg=row_bg,
                   halign='center' if ci == 1 else 'left')
        ws2.row_dimensions[ri].height = 20

    # Total row
    tr = 5 + len(subjects)
    ws2.merge_cells('A{}:B{}'.format(tr, tr))
    _wcell(ws2, tr, 1, 'Total Subjects Registered',
           bold=True, size=10, bg='E8F4FD', fg='1F3864', halign='right')
    _wcell(ws2, tr, 3, len(subjects),
           bold=True, size=10, bg='E8F4FD', fg='1F3864', halign='center')
    ws2.row_dimensions[tr].height = 20

    ws2.column_dimensions['A'].width = 8
    ws2.column_dimensions['B'].width = 20
    ws2.column_dimensions['C'].width = 36

    # ── SELF-CHECK ───────────────────────────────────────────
    assert len(wb.sheetnames) == 2, f"Expected 2 sheets, got {len(wb.sheetnames)}"
    assert wb.sheetnames[0] == 'Form Details'
    assert wb.sheetnames[1] == 'Subject Details'

    # Verify no banned content
    for ws in [ws1, ws2]:
        for row in ws.iter_rows():
            for cell in row:
                val = str(cell.value or '')
                assert 'Confidence' not in val, f"Cell {cell.coordinate} contains 'Confidence'"
                assert 'Column_1' not in val, f"Cell {cell.coordinate} contains 'Column_1'"

    # Verify Sheet 2 structure
    header_cell = ws2.cell(row=4, column=1).value
    assert header_cell == header_labels[0], f"Sheet 2 row 4 col A: expected '{header_labels[0]}', got '{header_cell}'"

    wb.save(output_path)
    return output_path


def get_extraction_summary(pdf_path: str) -> dict:
    """
    Extract data from PDF and return a summary dict (for JSON output to route.js).
    Also generates the xlsx file.
    """
    import uuid

    output_dir = '/app/outputs'
    os.makedirs(output_dir, exist_ok=True)
    xlsx_id = str(uuid.uuid4())
    xlsx_path = os.path.join(output_dir, f'{xlsx_id}.xlsx')

    try:
        extract_and_build(pdf_path, xlsx_path)

        # Also extract raw data for JSON response
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            all_tables = page.extract_tables({
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines"
            })

            if not all_tables:
                return {
                    "columns": [],
                    "rows": [],
                    "document_type": "unknown",
                    "confidence": 0.0,
                    "error": "No tables found",
                    "xlsx_path": "",
                }

            rows = all_tables[0]

        # Parse metadata
        blob = re.sub(r'\n', ' ', rows[1][0] or '') if len(rows) > 1 and rows[1] and rows[1][0] else ''
        md = {
            "Institute Name": _get_field(r'Institute Name\s*:\s*(.+?)(?=Semester\s*:)', blob),
            "Semester": _get_field(r'Semester\s*:\s*:?\s*(.+?)(?=Enrollment No)', blob),
            "Enrollment No": _get_field(r'Enrollment No\s*:\s*(\S+)', blob),
            "Student Name": _get_field(r"Student's Name\s*:\s*:?\s*(\S+)", blob),
        }

        # Find table data
        header_idx = 2
        for i, r in enumerate(rows):
            if r and len(r) >= 2:
                cell0 = str(r[0] or '').strip().lower()
                if cell0 in ('sr.', 'sr', 'sno', 's.no', 'no.', '#', 'sl.'):
                    header_idx = i
                    break

        header_row = rows[header_idx] if header_idx < len(rows) else ['Sr.', 'Subject Code', 'Subject Name']
        columns = [str(v).strip() if v else f'Column_{i}' for i, v in enumerate(header_row[:3])]

        data_rows = []
        for r in rows[header_idx + 1:]:
            if _is_skip_row(r):
                continue
            row_dict = {}
            for ci, col in enumerate(columns):
                val = str(r[ci]).strip() if ci < len(r) and r[ci] else ''
                row_dict[col] = val
            if any(row_dict.values()):
                data_rows.append(row_dict)

        return {
            "columns": columns,
            "rows": data_rows,
            "document_type": "form",
            "confidence": 0.90,
            "extraction_method": "pdfplumber_lines",
            "xlsx_path": xlsx_path,
            "metadata": md,
        }

    except Exception as e:
        # Clean up failed xlsx
        if os.path.exists(xlsx_path):
            os.remove(xlsx_path)
        return {
            "columns": [],
            "rows": [],
            "document_type": "unknown",
            "confidence": 0.0,
            "error": str(e),
            "extraction_method": "pdfplumber_lines",
            "xlsx_path": "",
        }
