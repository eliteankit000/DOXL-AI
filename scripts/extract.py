#!/usr/bin/env python3
"""
DocXL AI — PDF-to-Excel Extraction Entry Point

Uses the pdfplumber-based pipeline (lib/pdf_engine/pipeline.py).
No LLM / GPT calls — pure deterministic extraction.

Usage:
    python scripts/extract.py <file_path>
"""
import sys
import os
import json
import time
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python extract.py <file_path>"}))
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(json.dumps({"error": f"File not found: {file_path}"}))
        sys.exit(1)

    print(f"[DEBUG] File: {file_path}", file=sys.stderr)
    print(f"[DEBUG] File size: {os.path.getsize(file_path)} bytes", file=sys.stderr)

    start_time = time.time()

    # ------------------------------------------------------------------
    # Import and run the new pdfplumber-based pipeline
    # ------------------------------------------------------------------
    try:
        sys.path.insert(0, '/app')
        from lib.pdf_engine.pipeline import process

        print("[DEBUG] Using pdfplumber pipeline", file=sys.stderr)
        result = process(file_path)

        tables = result.get("tables", [])
        metadata = result.get("metadata", {})
        source = result.get("source", "unreadable")
        success = result.get("success", False)

        print(f"[DEBUG] Pipeline source: {source}", file=sys.stderr)
        print(f"[DEBUG] Tables: {len(tables)}", file=sys.stderr)
        print(f"[DEBUG] Metadata fields: {len(metadata)}", file=sys.stderr)

        # Convert DataFrames to JSON-friendly {columns, rows} format
        if tables:
            import pandas as pd

            # Use the first table as the primary output
            primary = tables[0]
            columns = [str(c) for c in primary.columns.tolist()]
            rows = []
            for _, row in primary.iterrows():
                row_dict = {}
                for col in columns:
                    val = row[col]
                    if pd.isna(val):
                        val = ""
                    row_dict[col] = str(val) if val != "" else ""
                rows.append(row_dict)

            output = {
                "columns": columns,
                "rows": rows,
                "document_type": "table",
                "confidence": 0.90 if source in ("geometric", "text_align") else 0.70,
                "extraction_method": f"pdfplumber_{source}",
                "processing_time": time.time() - start_time,
            }

            # If metadata also found, include it
            if metadata:
                output["metadata"] = metadata

            print(f"[DEBUG] Output: {len(columns)} columns, {len(rows)} rows", file=sys.stderr)

        elif metadata:
            # Metadata-only output → build columns/rows from key-value pairs
            columns = ["Field", "Value"]
            rows = [{"Field": k, "Value": v} for k, v in metadata.items()]
            output = {
                "columns": columns,
                "rows": rows,
                "document_type": "form",
                "confidence": 0.65,
                "extraction_method": f"pdfplumber_{source}",
                "processing_time": time.time() - start_time,
            }
            print(f"[DEBUG] Metadata output: {len(rows)} fields", file=sys.stderr)

        else:
            output = {
                "columns": [],
                "rows": [],
                "document_type": "unknown",
                "confidence": 0.0,
                "error": "No structured data could be extracted",
                "extraction_method": f"pdfplumber_{source}",
                "processing_time": time.time() - start_time,
            }
            print("[DEBUG] No data extracted", file=sys.stderr)

    except Exception as e:
        print(f"[DEBUG] Fatal error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        output = {
            "columns": [],
            "rows": [],
            "document_type": "unknown",
            "confidence": 0.0,
            "error": f"Extraction failed: {str(e)}",
            "processing_time": time.time() - start_time,
        }

    # Output result as JSON to stdout
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
