#!/usr/bin/env python3
"""
PDF Extractor Bug Fixes Testing Suite
Tests the specific bug fixes in /app/lib/pdf_engine/extractor.py
"""

import sys
import os
import requests
import json

# Add the app directory to Python path
sys.path.insert(0, '/app')

def test_is_column_header_line_function():
    """
    TEST 1: _is_column_header_line Function (CRITICAL - Bug 1)
    """
    print("=" * 60)
    print("TEST 1: _is_column_header_line Function")
    print("=" * 60)
    
    try:
        from lib.pdf_engine.extractor import _is_column_header_line
        
        # Test data
        column_header_text = 'ITEM NAME OPENING STOCK PURCHASED CONSUPTION WASTAGE CLOSING STOCK'
        headers = [['ITEM NAME', 'OPENING STOCK', 'PURCHASED', 'CONSUPTION', 'WASTAGE', 'CLOSING STOCK']]
        real_title = 'HOTEL KANCHAN BAR INVENTORY REPORT 08/04/2026'
        short_text = 'TEST'
        
        # Test 1: Column header text should return True
        result1 = _is_column_header_line(column_header_text, headers)
        print(f"✅ Test 1.1: Column header text detection")
        print(f"   Input: '{column_header_text}'")
        print(f"   Headers: {headers[0]}")
        print(f"   Result: {result1} (Expected: True)")
        assert result1 == True, f"Expected True, got {result1}"
        
        # Test 2: Real title should return False
        result2 = _is_column_header_line(real_title, headers)
        print(f"✅ Test 1.2: Real title text detection")
        print(f"   Input: '{real_title}'")
        print(f"   Headers: {headers[0]}")
        print(f"   Result: {result2} (Expected: False)")
        assert result2 == False, f"Expected False, got {result2}"
        
        # Test 3: Short text should return False (less than 3 uppercase words)
        result3 = _is_column_header_line(short_text, headers)
        print(f"✅ Test 1.3: Short text detection")
        print(f"   Input: '{short_text}'")
        print(f"   Headers: {headers[0]}")
        print(f"   Result: {result3} (Expected: False)")
        assert result3 == False, f"Expected False, got {result3}"
        
        print("✅ TEST 1 PASSED: _is_column_header_line function working correctly")
        return True
        
    except Exception as e:
        print(f"❌ TEST 1 FAILED: {str(e)}")
        return False

def test_title_selection_logic():
    """
    TEST 2: Title Selection Logic (CRITICAL - Bug 1)
    """
    print("\n" + "=" * 60)
    print("TEST 2: Title Selection Logic")
    print("=" * 60)
    
    try:
        from lib.pdf_engine.extractor import _is_column_header_line
        
        # Simulate the title selection logic from extract_pdf_content
        lines = [
            'BAR INVENTORY REPORT 08/04/2026',
            'HOTEL KANCHAN BAR INVENTORY REPORT 08/04/2026',
            'ITEM NAME OPENING STOCK PURCHASED CONSUPTION WASTAGE CLOSING STOCK'
        ]
        
        table_headers = [['ITEM NAME', 'OPENING STOCK', 'PURCHASED', 'CONSUPTION', 'WASTAGE', 'CLOSING STOCK']]
        
        # Filter out column header lines (simulate the logic from extract_pdf_content)
        title_candidates = []
        for line in lines:
            line = line.strip()
            if len(line) <= 8:
                continue
            if _is_column_header_line(line, table_headers):
                print(f"   Filtered out column header: '{line}'")
                continue
            title_candidates.append(line)
        
        print(f"✅ Test 2.1: Title candidates after filtering")
        print(f"   Original lines: {lines}")
        print(f"   Filtered candidates: {title_candidates}")
        
        # Select the longest candidate (as per the code)
        if title_candidates:
            doc_title = max(title_candidates, key=len)
        else:
            doc_title = "Document"
        
        print(f"✅ Test 2.2: Final title selection")
        print(f"   Selected title: '{doc_title}'")
        print(f"   Expected: 'HOTEL KANCHAN BAR INVENTORY REPORT 08/04/2026'")
        
        # Verify the column header line was excluded
        column_header_line = 'ITEM NAME OPENING STOCK PURCHASED CONSUPTION WASTAGE CLOSING STOCK'
        assert doc_title != column_header_line, f"Column header line should not be selected as title"
        assert doc_title == 'HOTEL KANCHAN BAR INVENTORY REPORT 08/04/2026', f"Expected specific title, got {doc_title}"
        
        print("✅ TEST 2 PASSED: Title selection logic working correctly")
        return True
        
    except Exception as e:
        print(f"❌ TEST 2 FAILED: {str(e)}")
        return False

def test_source_code_structure():
    """
    TEST 3: Source Code Structure Verification (Speed)
    """
    print("\n" + "=" * 60)
    print("TEST 3: Source Code Structure Verification")
    print("=" * 60)
    
    try:
        # Read the source file
        with open('/app/lib/pdf_engine/extractor.py', 'r') as f:
            source_code = f.read()
        
        # Check for required strings
        checks = [
            ('join_tolerance', 'join_tolerance string in geometric extraction params'),
            ('edge_min_length', 'edge_min_length string in geometric extraction params'),
            ('if tables_geo:', 'text fallback conditional'),
            ('layout=False', 'layout=False parameter'),
            ('col_widths = [len(str(h)) for h in headers]', 'inline width tracking'),
            ('col_widths[ci-1] = max(', 'inline width update'),
            ('pdfplumber.open', 'pdfplumber.open usage')
        ]
        
        for check_string, description in checks:
            if check_string in source_code:
                print(f"✅ Found: {description}")
            else:
                print(f"❌ Missing: {description}")
                raise AssertionError(f"Missing required string: {check_string}")
        
        # Verify pdfplumber.open appears exactly once
        pdfplumber_count = source_code.count('pdfplumber.open')
        print(f"✅ pdfplumber.open count: {pdfplumber_count} (Expected: 1)")
        assert pdfplumber_count == 1, f"Expected pdfplumber.open to appear exactly once, found {pdfplumber_count}"
        
        print("✅ TEST 3 PASSED: Source code structure verification complete")
        return True
        
    except Exception as e:
        print(f"❌ TEST 3 FAILED: {str(e)}")
        return False

def test_title_extraction_after_tables():
    """
    TEST 4: Title Extraction Happens AFTER Tables
    """
    print("\n" + "=" * 60)
    print("TEST 4: Title Extraction Happens AFTER Tables")
    print("=" * 60)
    
    try:
        # Read the source file
        with open('/app/lib/pdf_engine/extractor.py', 'r') as f:
            source_code = f.read()
        
        # Find positions of key code blocks
        # Look for the comment that indicates title extraction after tables
        title_comment_pos = source_code.find('# ── Document title from page 1 (AFTER tables)')
        table_processing_pos = source_code.find('all_tables.append')
        
        print(f"✅ Table processing position: {table_processing_pos}")
        print(f"✅ Title extraction comment position: {title_comment_pos}")
        
        if table_processing_pos == -1:
            raise AssertionError("Could not find table processing code (all_tables.append)")
        
        if title_comment_pos == -1:
            raise AssertionError("Could not find title extraction comment")
        
        # Verify title extraction comes after table processing
        assert title_comment_pos > table_processing_pos, \
            f"Title extraction should come after table processing. Found at {title_comment_pos}, table processing at {table_processing_pos}"
        
        # Also verify the actual title extraction logic is in the right place
        title_logic_pos = source_code.find('if page_num == 0:', title_comment_pos)
        if title_logic_pos == -1:
            raise AssertionError("Could not find title extraction logic after comment")
        
        print(f"✅ Title extraction logic position: {title_logic_pos}")
        assert title_logic_pos > table_processing_pos, \
            f"Title extraction logic should come after table processing. Found at {title_logic_pos}, table processing at {table_processing_pos}"
        
        print("✅ TEST 4 PASSED: Title extraction correctly happens AFTER table processing")
        return True
        
    except Exception as e:
        print(f"❌ TEST 4 FAILED: {str(e)}")
        return False

def test_multi_page_continuation_regression():
    """
    TEST 5: Multi-Page Continuation Regression
    """
    print("\n" + "=" * 60)
    print("TEST 5: Multi-Page Continuation Regression")
    print("=" * 60)
    
    try:
        from lib.pdf_engine.extractor import _looks_like_data_row
        
        # Read the source file to verify initialization
        with open('/app/lib/pdf_engine/extractor.py', 'r') as f:
            source_code = f.read()
        
        # Check for proper variable initialization before page loop
        init_check1 = 'last_known_headers = []' in source_code
        init_check2 = 'last_known_num_cols = 0' in source_code
        
        print(f"✅ Test 5.1: Variable initialization check")
        print(f"   last_known_headers = [] found: {init_check1}")
        print(f"   last_known_num_cols = 0 found: {init_check2}")
        
        assert init_check1, "last_known_headers = [] initialization not found"
        assert init_check2, "last_known_num_cols = 0 initialization not found"
        
        # Test _looks_like_data_row function
        print(f"✅ Test 5.2: _looks_like_data_row function test")
        
        # Test with bar data
        bar_data = ['OLD MONK', '0 BOTTEL | 510 ML', '0 BOTTEL | 00 ML']
        known_headers = ['ITEM NAME', 'OPENING STOCK', 'PURCHASED']
        
        result1 = _looks_like_data_row(bar_data, known_headers)
        print(f"   Bar data test: {bar_data}")
        print(f"   Known headers: {known_headers}")
        print(f"   Result: {result1} (Expected: True)")
        assert result1 == True, f"Expected True for bar data, got {result1}"
        
        # Test with repeated header (should return False)
        repeated_header = ['ITEM NAME', 'OPENING STOCK', 'PURCHASED']
        result2 = _looks_like_data_row(repeated_header, known_headers)
        print(f"   Repeated header test: {repeated_header}")
        print(f"   Known headers: {known_headers}")
        print(f"   Result: {result2} (Expected: False)")
        assert result2 == False, f"Expected False for repeated header, got {result2}"
        
        print("✅ TEST 5 PASSED: Multi-page continuation regression tests complete")
        return True
        
    except Exception as e:
        print(f"❌ TEST 5 FAILED: {str(e)}")
        return False

def test_health_check_api():
    """
    TEST 6: Health Check API
    """
    print("\n" + "=" * 60)
    print("TEST 6: Health Check API")
    print("=" * 60)
    
    try:
        # Read the base URL from environment
        try:
            with open('/app/.env', 'r') as f:
                env_content = f.read()
            
            base_url = None
            for line in env_content.split('\n'):
                if line.startswith('NEXT_PUBLIC_BASE_URL='):
                    base_url = line.split('=', 1)[1].strip()
                    break
            
            if not base_url:
                raise ValueError("NEXT_PUBLIC_BASE_URL not found in .env")
            
            print(f"✅ Base URL from .env: {base_url}")
            
        except Exception as e:
            print(f"⚠️  Could not read .env file: {e}")
            base_url = "http://localhost:3000"  # fallback
            print(f"✅ Using fallback URL: {base_url}")
        
        # Test health check endpoint
        health_url = f"{base_url}/api/health"
        print(f"✅ Testing health check: {health_url}")
        
        response = requests.get(health_url, timeout=10)
        print(f"✅ Response status: {response.status_code}")
        print(f"✅ Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Response data: {data}")
                
                # Verify expected fields
                assert 'status' in data, "Missing 'status' field in response"
                assert data['status'] == 'ok', f"Expected status 'ok', got {data['status']}"
                
                print("✅ TEST 6 PASSED: Health check API working correctly")
                return True
                
            except json.JSONDecodeError:
                print(f"✅ Response text: {response.text}")
                print("✅ TEST 6 PASSED: Health check API responding (non-JSON response)")
                return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"❌ Response text: {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ TEST 6 FAILED: {str(e)}")
        return False

def main():
    """
    Run all PDF extractor bug fix tests
    """
    print("PDF EXTRACTOR BUG FIXES TESTING SUITE")
    print("=" * 60)
    
    tests = [
        test_is_column_header_line_function,
        test_title_selection_logic,
        test_source_code_structure,
        test_title_extraction_after_tables,
        test_multi_page_continuation_regression,
        test_health_check_api
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {str(e)}")
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)