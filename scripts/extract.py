#!/usr/bin/env python3
"""
DocXL AI — PDF-to-Excel Extraction Entry Point

Calls extract_and_build() to generate a styled .xlsx file directly.
Outputs JSON with extraction summary to stdout.

Usage:
    python scripts/extract.py <file_path>
"""
import sys
import os
import json
import time


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python extract.py <file_path>"}))
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(json.dumps({"error": f"File not found: {file_path}"}))
        sys.exit(1)

    print(f"[extract] File: {file_path}", file=sys.stderr)
    print(f"[extract] Size: {os.path.getsize(file_path)} bytes", file=sys.stderr)

    start_time = time.time()

    try:
        sys.path.insert(0, '/app')
        from lib.pdf_engine.extractor import get_extraction_summary

        result = get_extraction_summary(file_path)
        result["processing_time"] = time.time() - start_time

        xlsx_path = result.get("xlsx_path", "")
        if xlsx_path and os.path.exists(xlsx_path):
            print(f"[extract] xlsx generated: {xlsx_path} ({os.path.getsize(xlsx_path)} bytes)", file=sys.stderr)
        else:
            print("[extract] WARNING: No xlsx file generated", file=sys.stderr)

        print(f"[extract] Columns: {len(result.get('columns', []))}", file=sys.stderr)
        print(f"[extract] Rows: {len(result.get('rows', []))}", file=sys.stderr)
        print(f"[extract] Method: {result.get('extraction_method', 'unknown')}", file=sys.stderr)

    except Exception as e:
        print(f"[extract] Fatal error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        result = {
            "columns": [],
            "rows": [],
            "document_type": "unknown",
            "confidence": 0.0,
            "error": f"Extraction failed: {str(e)}",
            "processing_time": time.time() - start_time,
            "xlsx_path": "",
        }

    # Output result as JSON to stdout
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
