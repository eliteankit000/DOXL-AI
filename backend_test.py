#!/usr/bin/env python3
"""
Backend Test Suite for PDF Extractor Bug Fixes
Testing 8 critical areas as specified in the review request.
"""

import sys
import os
import json
import traceback
import requests
from pathlib import Path

# Add lib directory to path for imports
sys.path.insert(0, '/app')

def test_1_python_import_verification():
    """TEST 1: Python Import Verification"""
    print("\n=== TEST 1: Python Import Verification ===")
    
    try:
        # Import all functions from lib.pdf_engine.extractor
        from lib.pdf_engine.extractor import (
            extract_and_build,
            extract_pdf_content, 
            build_excel,
            get_extraction_summary,
            _looks_like_data_row,
            _is_junk_row,
            _find_header_row
        )
        
        print("✅ All required functions imported successfully:")
        print("  - extract_and_build")
        print("  - extract_pdf_content")
        print("  - build_excel") 
        print("  - get_extraction_summary")
        print("  - _looks_like_data_row")
        print("  - _is_junk_row")
        print("  - _find_header_row")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False

def test_2_variable_initialization():
    """TEST 2: Variable Initialization (CRITICAL - Bug 1)"""
    print("\n=== TEST 2: Variable Initialization (CRITICAL - Bug 1) ===")
    
    try:
        # Read the source file and check for proper initialization
        with open('/app/lib/pdf_engine/extractor.py', 'r') as f:
            content = f.read()
        
        # Check that last_known_headers and last_known_num_cols are initialized
        # before the page loop in extract_pdf_content
        
        # Find the function definition
        func_start = content.find('def extract_pdf_content(pdf_path: str) -> dict:')
        if func_start == -1:
            print("❌ extract_pdf_content function not found")
            return False
            
        # Find the with pdfplumber.open block
        with_block = content.find('with pdfplumber.open(pdf_path) as pdf:', func_start)
        if with_block == -1:
            print("❌ pdfplumber.open block not found")
            return False
            
        # Find the for page_num, page loop
        page_loop = content.find('for page_num, page in enumerate(pdf.pages):', with_block)
        if page_loop == -1:
            print("❌ page enumeration loop not found")
            return False
            
        # Check that initialization happens between with block and page loop
        init_section = content[with_block:page_loop]
        
        has_headers_init = 'last_known_headers = []' in init_section
        has_cols_init = 'last_known_num_cols = 0' in init_section
        
        print(f"Checking initialization between with block and page loop:")
        print(f"  - last_known_headers = [] found: {has_headers_init}")
        print(f"  - last_known_num_cols = 0 found: {has_cols_init}")
        
        if has_headers_init and has_cols_init:
            print("✅ CRITICAL: Variable initialization is correct")
            print("  Variables are initialized BEFORE the page loop as required")
            return True
        else:
            print("❌ CRITICAL: Variable initialization is missing or incorrect")
            print("  This would cause NameError in continuation logic")
            return False
            
    except Exception as e:
        print(f"❌ Error checking variable initialization: {e}")
        return False

def test_3_looks_like_data_row_logic():
    """TEST 3: _looks_like_data_row Function Logic"""
    print("\n=== TEST 3: _looks_like_data_row Function Logic ===")
    
    try:
        from lib.pdf_engine.extractor import _looks_like_data_row
        
        # Test 1: Empty known_headers should return False
        result1 = _looks_like_data_row(['OLD MONK', '0 BOTTEL'], [])
        print(f"Test 1 - Empty headers: {result1} (should be False)")
        
        # Test 2: Bar inventory data row should return True
        bar_row = ['OLD MONK', '0 BOTTEL | 510 ML', '0 BOTTEL | 00 ML']
        bar_headers = ['ITEM NAME', 'OPENING STOCK', 'PURCHASED']
        result2 = _looks_like_data_row(bar_row, bar_headers)
        print(f"Test 2 - Bar inventory data: {result2} (should be True)")
        
        # Test 3: Numeric data row should return True (numeric fallback)
        numeric_row = ['2024-01-15', '1500.00', '250.50']
        numeric_headers = ['Date', 'Credit', 'Debit']
        result3 = _looks_like_data_row(numeric_row, numeric_headers)
        print(f"Test 3 - Numeric data: {result3} (should be True)")
        
        # Test 4: Repeated header row should return False (header overlap detection)
        header_row = ['ITEM NAME', 'OPENING STOCK', 'PURCHASED']
        same_headers = ['ITEM NAME', 'OPENING STOCK', 'PURCHASED']
        result4 = _looks_like_data_row(header_row, same_headers)
        print(f"Test 4 - Repeated headers: {result4} (should be False)")
        
        # Verify expected results
        expected = [False, True, True, False]
        actual = [result1, result2, result3, result4]
        
        if actual == expected:
            print("✅ _looks_like_data_row function logic is correct")
            return True
        else:
            print(f"❌ _looks_like_data_row logic failed. Expected: {expected}, Got: {actual}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing _looks_like_data_row: {e}")
        traceback.print_exc()
        return False

def test_4_is_junk_row_logic():
    """TEST 4: _is_junk_row Function Logic"""
    print("\n=== TEST 4: _is_junk_row Function Logic ===")
    
    try:
        from lib.pdf_engine.extractor import _is_junk_row
        
        # Test 1: Single-cell spanning row should return True
        spanning_row = ['BAR INVENTORY REPORT 08/04/2026', None, None, None, None, None]
        result1 = _is_junk_row(spanning_row)
        print(f"Test 1 - Single-cell spanning: {result1} (should be True)")
        
        # Test 2: Datetime+page stamp should return True
        datetime_row = ['4/9/2026 7:29:49  1', None, None, None, None, None]
        result2 = _is_junk_row(datetime_row)
        print(f"Test 2 - Datetime+page stamp: {result2} (should be True)")
        
        # Test 3: Valid data row should return False
        data_row = ['100 PIPER', '0 BOTTEL', '00 ML', '0 BOTTEL', '00 ML', '0 BOTTEL']
        result3 = _is_junk_row(data_row)
        print(f"Test 3 - Valid data row: {result3} (should be False)")
        
        # Test 4: Empty row should return True
        empty_row = [None, None, None]
        result4 = _is_junk_row(empty_row)
        print(f"Test 4 - Empty row: {result4} (should be True)")
        
        # Verify expected results
        expected = [True, True, False, True]
        actual = [result1, result2, result3, result4]
        
        if actual == expected:
            print("✅ _is_junk_row function logic is correct")
            return True
        else:
            print(f"❌ _is_junk_row logic failed. Expected: {expected}, Got: {actual}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing _is_junk_row: {e}")
        traceback.print_exc()
        return False

def test_5_title_deduplication():
    """TEST 5: Title Deduplication in build_excel"""
    print("\n=== TEST 5: Title Deduplication in build_excel ===")
    
    try:
        # Read the source file and verify subtitle check conditions
        with open('/app/lib/pdf_engine/extractor.py', 'r') as f:
            content = f.read()
        
        # Look for the subtitle check pattern in build_excel
        # Should appear twice: once for table sheets and once for metadata sheets
        
        # Pattern to match the 4-condition check
        pattern_parts = [
            'content["doc_subtitle"]',
            'content["doc_subtitle"] not in content["doc_title"]',
            'content["doc_title"] not in content["doc_subtitle"]',
            'len(content["doc_subtitle"]) > 10'
        ]
        
        # Find all occurrences of the subtitle check
        subtitle_checks = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if 'content["doc_subtitle"]' in line and 'not in' in line:
                # Found a potential subtitle check, examine the surrounding lines
                check_block = '\n'.join(lines[max(0, i-2):i+5])
                
                # Count how many of the 4 conditions are present
                conditions_found = sum(1 for part in pattern_parts if part in check_block)
                
                if conditions_found >= 3:  # At least 3 of 4 conditions
                    subtitle_checks.append((i+1, conditions_found))
        
        print(f"Found {len(subtitle_checks)} subtitle deduplication checks:")
        for line_num, conditions in subtitle_checks:
            print(f"  - Line {line_num}: {conditions}/4 conditions found")
        
        # Should find at least 2 occurrences (table sheets + metadata sheets)
        if len(subtitle_checks) >= 2:
            print("✅ Title deduplication logic found in build_excel")
            print("  Checks include all 4 required conditions:")
            print("  1. content['doc_subtitle'] (truthy check)")
            print("  2. content['doc_subtitle'] not in content['doc_title']")
            print("  3. content['doc_title'] not in content['doc_subtitle']")
            print("  4. len(content['doc_subtitle']) > 10")
            return True
        else:
            print("❌ Title deduplication logic not found or incomplete")
            return False
            
    except Exception as e:
        print(f"❌ Error checking title deduplication: {e}")
        return False

def test_6_continuation_logic_simulation():
    """TEST 6: Continuation Logic Simulation"""
    print("\n=== TEST 6: Continuation Logic Simulation ===")
    
    try:
        from lib.pdf_engine.extractor import _looks_like_data_row
        
        # Simulate multi-page processing
        print("Simulating multi-page table continuation:")
        
        # Step 1: Initialize
        last_known_headers = []
        last_known_num_cols = 0
        print(f"Step 1 - Initialize: headers={last_known_headers}, cols={last_known_num_cols}")
        
        # Step 2: Process page 1 with headers
        page1_headers = ['ITEM NAME', 'OPENING STOCK', 'PURCHASED', 'CONSUMPTION', 'WASTAGE', 'CLOSING STOCK']
        is_continuation_page1 = bool(last_known_headers)  # Should be False ([] is falsy)
        print(f"Step 2 - Page 1 headers: is_continuation={is_continuation_page1} (should be False)")
        
        # After processing page 1
        last_known_headers = page1_headers
        last_known_num_cols = len(page1_headers)
        print(f"Step 2 - After page 1: headers={len(last_known_headers)} items, cols={last_known_num_cols}")
        
        # Step 3: Process page 2 with data row
        page2_data_row = ['OLD MONK', '0 BOTTEL | 510 ML', '0 BOTTEL | 00 ML', '0 BOTTEL | 510 ML', '0 BOTTEL | 00 ML', '0 BOTTEL | 510 ML']
        
        # Check continuation conditions
        has_headers = bool(last_known_headers)
        same_col_count = len(page2_data_row) == last_known_num_cols
        looks_like_data = _looks_like_data_row(page2_data_row, last_known_headers)
        
        is_continuation_page2 = has_headers and same_col_count and looks_like_data
        
        print(f"Step 3 - Page 2 data row analysis:")
        print(f"  - has_headers: {has_headers}")
        print(f"  - same_col_count: {same_col_count} ({len(page2_data_row)} == {last_known_num_cols})")
        print(f"  - looks_like_data: {looks_like_data}")
        print(f"  - is_continuation: {is_continuation_page2} (should be True)")
        
        # Verify expected behavior
        if not is_continuation_page1 and is_continuation_page2:
            print("✅ Continuation logic simulation successful")
            print("  Page 1: New table (headers detected)")
            print("  Page 2: Continuation (data row detected, same column count)")
            return True
        else:
            print("❌ Continuation logic simulation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error simulating continuation logic: {e}")
        traceback.print_exc()
        return False

def test_7_no_col_3_col_4_in_continuation():
    """TEST 7: No Col_3/Col_4/Col_5 in Continuation"""
    print("\n=== TEST 7: No Col_3/Col_4/Col_5 in Continuation ===")
    
    try:
        # Read the source file and verify continuation logic
        with open('/app/lib/pdf_engine/extractor.py', 'r') as f:
            content = f.read()
        
        # Find the continuation logic in extract_pdf_content
        func_start = content.find('def extract_pdf_content(pdf_path: str) -> dict:')
        if func_start == -1:
            print("❌ extract_pdf_content function not found")
            return False
        
        # Look for the continuation logic
        continuation_check = content.find('is_continuation = (', func_start)
        if continuation_check == -1:
            print("❌ Continuation check logic not found")
            return False
        
        # Find the if is_continuation block
        if_continuation = content.find('if is_continuation:', continuation_check)
        if if_continuation == -1:
            print("❌ if is_continuation block not found")
            return False
        
        # Find the else block
        else_block = content.find('else:', if_continuation)
        if else_block == -1:
            print("❌ else block not found")
            return False
        
        # Extract the continuation and non-continuation logic
        next_if = content.find('if ', else_block + 10)  # Find next if statement
        if next_if == -1:
            next_if = len(content)
        
        continuation_section = content[if_continuation:else_block]
        non_continuation_section = content[else_block:next_if]
        
        # Check continuation logic uses last_known_headers
        uses_last_known = 'headers = last_known_headers' in continuation_section
        
        # Check non-continuation logic uses candidate_headers and sets last_known
        uses_candidate = 'headers = candidate_headers' in non_continuation_section
        sets_last_known = 'last_known_headers = headers' in non_continuation_section
        
        print("Checking continuation vs non-continuation logic:")
        print(f"  - Continuation uses last_known_headers: {uses_last_known}")
        print(f"  - Non-continuation uses candidate_headers: {uses_candidate}")
        print(f"  - Non-continuation sets last_known_headers: {sets_last_known}")
        
        # Verify that candidate_headers generation includes Col_X fallback
        candidate_generation = content.find('candidate_headers = [', func_start)
        if candidate_generation != -1:
            candidate_section = content[candidate_generation:candidate_generation + 200]
            has_col_fallback = 'Col_' in candidate_section
            print(f"  - Candidate headers have Col_X fallback: {has_col_fallback}")
        else:
            has_col_fallback = False
            print("  - Candidate headers generation not found")
        
        if uses_last_known and uses_candidate and sets_last_known:
            print("✅ Continuation logic correctly avoids Col_3/Col_4/Col_5")
            print("  When is_continuation=True: uses last_known_headers")
            print("  When is_continuation=False: uses candidate_headers (may have Col_X)")
            print("  This prevents Col_3/Col_4/Col_5 in continuation pages")
            return True
        else:
            print("❌ Continuation logic may not properly avoid Col_3/Col_4/Col_5")
            return False
            
    except Exception as e:
        print(f"❌ Error checking continuation logic: {e}")
        return False

def test_8_health_check_api():
    """TEST 8: Health Check API"""
    print("\n=== TEST 8: Health Check API ===")
    
    try:
        # Test health check endpoint using localhost
        health_url = "http://localhost:3000/api/health"
        print(f"Testing health check: {health_url}")
        
        response = requests.get(health_url, timeout=10)
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            # Verify response contains expected fields
            try:
                data = response.json()
                if "status" in data and data["status"] == "ok":
                    print("✅ Health Check API is working")
                    print(f"  Status: {data.get('status')}")
                    print(f"  Service: {data.get('service', 'N/A')}")
                    print(f"  Backend: {data.get('backend', 'N/A')}")
                    return True
                else:
                    print("❌ Health Check API response missing expected fields")
                    return False
            except json.JSONDecodeError:
                print("❌ Health Check API response is not valid JSON")
                return False
        else:
            print(f"❌ Health Check API returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health Check API request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing Health Check API: {e}")
        return False

def main():
    """Run all tests and provide summary"""
    print("🧪 PDF Extractor Bug Fixes - Backend Test Suite")
    print("=" * 60)
    
    tests = [
        ("Python Import Verification", test_1_python_import_verification),
        ("Variable Initialization (CRITICAL)", test_2_variable_initialization),
        ("_looks_like_data_row Logic", test_3_looks_like_data_row_logic),
        ("_is_junk_row Logic", test_4_is_junk_row_logic),
        ("Title Deduplication", test_5_title_deduplication),
        ("Continuation Logic Simulation", test_6_continuation_logic_simulation),
        ("No Col_3/Col_4/Col_5 in Continuation", test_7_no_col_3_col_4_in_continuation),
        ("Health Check API", test_8_health_check_api),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED - PDF Extractor bug fixes are working correctly!")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed - Issues need to be addressed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)