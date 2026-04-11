"""
DocXL AI — Pipeline Router

Routing order:
  1. extract_tables_geometric
  2. extract_tables_text_alignment
  3. extract_metadata_regex on raw pdfplumber text
  4. Raw text dump (unreadable)

Result object:
  {
    "tables": [pd.DataFrame, ...],
    "metadata": dict,
    "source": str,          # geometric | text_align | regex_fallback | unreadable
    "success": bool
  }
"""
import sys
import warnings
import logging
from typing import Dict, Any, List

import pdfplumber
import pandas as pd

from .extractor import (
    extract_tables_geometric,
    extract_tables_text_alignment,
    extract_metadata_regex,
)

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=UserWarning)


def _tables_to_dataframes(raw_tables: List[List[list]]) -> List[pd.DataFrame]:
    """Convert list-of-list tables to DataFrames (first row = header)."""
    dataframes: List[pd.DataFrame] = []
    for table in raw_tables:
        if not table or len(table) < 2:
            continue
        headers = table[0]
        data = table[1:]
        # Deduplicate empty headers
        seen = {}
        unique_headers = []
        for h in headers:
            h = h if h else 'Column'
            if h in seen:
                seen[h] += 1
                unique_headers.append(f"{h}_{seen[h]}")
            else:
                seen[h] = 0
                unique_headers.append(h)
        try:
            df = pd.DataFrame(data, columns=unique_headers)
            # Drop fully-empty columns
            df = df.dropna(axis=1, how='all')
            df = df.loc[:, ~(df == '').all()]
            if not df.empty and len(df.columns) >= 1:
                dataframes.append(df)
        except Exception:
            continue
    return dataframes


def _extract_full_text(pdf_path: str) -> str:
    """Extract full plain-text from all pages."""
    text_parts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:20]:  # safety limit
                page_text = page.extract_text() or ''
                if page_text.strip():
                    text_parts.append(page_text)
    except Exception:
        pass
    return '\n'.join(text_parts)


def process(pdf_path: str) -> Dict[str, Any]:
    """
    Main pipeline entry point.

    Returns:
        {
            "tables": [pd.DataFrame, ...],
            "metadata": dict,
            "source": str,
            "success": bool
        }
    """
    result: Dict[str, Any] = {
        "tables": [],
        "metadata": {},
        "source": "unreadable",
        "success": False,
    }

    # ── STRATEGY 1: Geometric (ruled lines) ──────────────────
    print("[pipeline] Trying geometric strategy...", file=sys.stderr)
    raw = extract_tables_geometric(pdf_path)
    if raw:
        dfs = _tables_to_dataframes(raw)
        if dfs:
            result["tables"] = dfs
            result["source"] = "geometric"
            result["success"] = True
            print(f"[pipeline] Geometric: {len(dfs)} table(s)", file=sys.stderr)
            return result

    # ── STRATEGY 2: Text alignment ───────────────────────────
    print("[pipeline] Trying text-alignment strategy...", file=sys.stderr)
    raw = extract_tables_text_alignment(pdf_path)
    if raw:
        dfs = _tables_to_dataframes(raw)
        if dfs:
            result["tables"] = dfs
            result["source"] = "text_align"
            result["success"] = True
            print(f"[pipeline] Text-align: {len(dfs)} table(s)", file=sys.stderr)
            return result

    # ── STRATEGY 3: Regex metadata from full text ────────────
    print("[pipeline] Trying regex fallback...", file=sys.stderr)
    full_text = _extract_full_text(pdf_path)
    if full_text.strip():
        metadata = extract_metadata_regex(full_text)
        if metadata:
            result["metadata"] = metadata
            result["source"] = "regex_fallback"
            result["success"] = True
            print(f"[pipeline] Regex: {len(metadata)} fields", file=sys.stderr)
            return result

    # ── STRATEGY 4: Raw text dump ────────────────────────────
    if full_text.strip():
        # Build a single-column DataFrame from lines
        lines = [line.strip() for line in full_text.splitlines() if line.strip()]
        if lines:
            df = pd.DataFrame({"Content": lines})
            result["tables"] = [df]
            result["source"] = "unreadable"
            result["success"] = True
            logger.warning("All strategies failed for %s — returning raw text.", pdf_path)
            print(f"[pipeline] WARNING: Raw text dump ({len(lines)} lines) for {pdf_path}", file=sys.stderr)
            return result

    logger.warning("Completely unreadable: %s", pdf_path)
    print(f"[pipeline] WARNING: Completely unreadable: {pdf_path}", file=sys.stderr)
    return result
