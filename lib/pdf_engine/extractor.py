"""
DocXL AI — pdfplumber-based PDF Table Extractor

Three extraction strategies:
  1. extract_tables_geometric  – ruled-line tables
  2. extract_tables_text_alignment – text-aligned tables
  3. extract_metadata_regex – free-form Label:Value pairs
"""
import re
import pdfplumber
from typing import List, Optional, Dict


# ─────────────────────────────────────────────
# 1. GEOMETRIC STRATEGY (lines / lines_strict)
# ─────────────────────────────────────────────

def extract_tables_geometric(pdf_path: str) -> Optional[List[List[list]]]:
    """
    Uses pdfplumber with vertical_strategy='lines', horizontal_strategy='lines'.
    Returns list of raw table arrays if any tables found, else None.
    Tries 'lines_strict' first, falls back to 'lines' if no results.
    """
    try:
        tables: List[List[list]] = []

        # Pass 1 — strict lines
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                try:
                    page_tables = page.extract_tables({
                        "vertical_strategy": "lines_strict",
                        "horizontal_strategy": "lines_strict",
                    })
                    if page_tables:
                        for t in page_tables:
                            cleaned = _clean_table(t)
                            if cleaned:
                                tables.append(cleaned)
                except Exception:
                    continue

        if tables:
            return tables

        # Pass 2 — relaxed lines
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                try:
                    page_tables = page.extract_tables({
                        "vertical_strategy": "lines",
                        "horizontal_strategy": "lines",
                    })
                    if page_tables:
                        for t in page_tables:
                            cleaned = _clean_table(t)
                            if cleaned:
                                tables.append(cleaned)
                except Exception:
                    continue

        return tables if tables else None

    except Exception as exc:
        print(f"[extractor] geometric error: {exc}")
        return None


# ─────────────────────────────────────────────
# 2. TEXT-ALIGNMENT STRATEGY
# ─────────────────────────────────────────────

def extract_tables_text_alignment(pdf_path: str) -> Optional[List[List[list]]]:
    """
    Uses pdfplumber with vertical_strategy='text', horizontal_strategy='text'.
    Only called when geometric strategy returns None.
    """
    try:
        tables: List[List[list]] = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                try:
                    page_tables = page.extract_tables({
                        "vertical_strategy": "text",
                        "horizontal_strategy": "text",
                        "snap_y_tolerance": 5,
                        "snap_x_tolerance": 5,
                        "join_y_tolerance": 5,
                        "join_x_tolerance": 5,
                    })
                    if page_tables:
                        for t in page_tables:
                            cleaned = _clean_table(t)
                            if cleaned:
                                tables.append(cleaned)
                except Exception:
                    continue

        return tables if tables else None

    except Exception as exc:
        print(f"[extractor] text_alignment error: {exc}")
        return None


# ─────────────────────────────────────────────
# 3. REGEX METADATA EXTRACTION
# ─────────────────────────────────────────────

def extract_metadata_regex(text_blob: str) -> Dict[str, str]:
    """
    Extracts key:value pairs from free-form Label : Value text blobs using regex.
    Returns a dict of field_name -> value.
    Handles multi-column layouts (two Label:Value pairs on same line).
    Returns '-' for any field not found, never raises.
    """
    metadata: Dict[str, str] = {}

    if not text_blob or not text_blob.strip():
        return metadata

    try:
        # Pattern: "Label  :  Value" or "Label: Value"
        # Handles multi-column lines with 2+ pairs
        pair_pattern = re.compile(
            r'([A-Za-z][A-Za-z0-9 /&._-]{1,40})'
            r'\s*[:=]\s*'
            r'([^\n:=]{1,200}?)'
            r'(?=\s{2,}[A-Za-z]|$)',
            re.MULTILINE,
        )

        for match in pair_pattern.finditer(text_blob):
            key = match.group(1).strip()
            value = match.group(2).strip()
            if key and value:
                # Normalise key
                norm_key = re.sub(r'\s+', ' ', key).title()
                metadata[norm_key] = value

        # Also try simple "Label: Value" per line (fallback)
        if not metadata:
            for line in text_blob.splitlines():
                line = line.strip()
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        k, v = parts[0].strip(), parts[1].strip()
                        if k and v and len(k) < 50:
                            metadata[k.title()] = v

    except Exception:
        pass

    return metadata


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _clean_table(raw_table: List[list]) -> Optional[List[list]]:
    """Remove fully-empty rows and None cells."""
    if not raw_table:
        return None

    cleaned = []
    for row in raw_table:
        cells = [(c or '').strip() for c in row]
        if any(cells):  # at least one non-empty cell
            cleaned.append(cells)

    # Need at least 2 rows (header + 1 data) and 2 columns
    if len(cleaned) < 2 or len(cleaned[0]) < 2:
        return None

    return cleaned
