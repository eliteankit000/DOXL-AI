#!/usr/bin/env python3
"""
DocXL AI - PDF-to-Excel Extraction Entry Point

Calls extract_and_build() to generate a styled .xlsx file directly.
Outputs JSON summary to stdout for route.js DB storage.

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
        print(json.dumps({"error": "File not found: {}".format(file_path)}))
        sys.exit(1)

    print("[extract] File: {}".format(file_path), file=sys.stderr)
    print("[extract] Size: {} bytes".format(os.path.getsize(file_path)), file=sys.stderr)

    start_time = time.time()

    try:
        sys.path.insert(0, '/app')
        from lib.pdf_engine.extractor import get_extraction_summary

        result = get_extraction_summary(file_path)
        result["processing_time"] = time.time() - start_time

        xlsx_path = result.get("xlsx_path", "")
        if xlsx_path and os.path.exists(xlsx_path):
            print("[extract] xlsx generated: {} ({} bytes)".format(
                xlsx_path, os.path.getsize(xlsx_path)), file=sys.stderr)
        else:
            print("[extract] WARNING: No xlsx file generated", file=sys.stderr)

        print("[extract] Columns: {}".format(len(result.get('columns', []))), file=sys.stderr)
        print("[extract] Rows: {}".format(len(result.get('rows', []))), file=sys.stderr)
        print("[extract] Method: {}".format(result.get('extraction_method', 'unknown')), file=sys.stderr)

    except Exception as exc:
        print("[extract] Fatal error: {}".format(str(exc)), file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        result = {
            "columns": [],
            "rows": [],
            "document_type": "unknown",
            "confidence": 0.0,
            "error": "Extraction failed: {}".format(str(exc)),
            "processing_time": time.time() - start_time,
            "xlsx_path": "",
        }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
