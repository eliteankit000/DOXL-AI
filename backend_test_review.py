#!/usr/bin/env python3
"""
DocXL AI Backend Testing Script - Review Request Tests
Tests specific endpoints and functionality as requested in the review.
"""

import requests
import json
import time
import sys
import subprocess
from typing import Dict, Any

# Base URL for testing
BASE_URL = "http://localhost:3000"
API_BASE = f"{BASE_URL}/api"

class BackendTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        # Set a reasonable timeout
        self.session.timeout = 30
        
    def log_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response_data": response_data
        })
    
    def test_health_check_api(self):
        """Test 1: GET /api/health — verify JSON response with status='ok'"""
        try:
            response = self.session.get(f"{API_BASE}/health")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    self.log_result("Health Check API", True, f"Status: {data.get('status')}, Backend: {data.get('backend', 'N/A')}")
                else:
                    self.log_result("Health Check API", False, f"Expected status='ok', got: {data}")
            else:
                self.log_result("Health Check API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Health Check API", False, f"Request failed: {str(e)}")
    
    def test_python_extract_syntax(self):
        """Test 2: Python extract.py syntax — run: python3 /app/scripts/extract.py 2>&1"""
        try:
            result = subprocess.run(
                ["python3", "/app/scripts/extract.py"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Should output JSON error about "No file path provided" (NOT a syntax/import error)
            if result.returncode != 0:
                output = result.stdout + result.stderr
                if "No file path provided" in output:
                    self.log_result("Python extract.py Syntax", True, "Expected 'No file path provided' error (syntax OK)")
                elif "OPENAI_API_KEY not configured" in output:
                    self.log_result("Python extract.py Syntax", True, "Expected OPENAI_API_KEY error (syntax OK)")
                elif "SyntaxError" in output or "ImportError" in output or "ModuleNotFoundError" in output:
                    self.log_result("Python extract.py Syntax", False, f"Syntax/Import error: {output}")
                else:
                    self.log_result("Python extract.py Syntax", True, f"Script ran without syntax errors: {output[:200]}")
            else:
                self.log_result("Python extract.py Syntax", True, "Script executed successfully")
                
        except subprocess.TimeoutExpired:
            self.log_result("Python extract.py Syntax", False, "Script execution timed out")
        except Exception as e:
            self.log_result("Python extract.py Syntax", False, f"Test failed: {str(e)}")
    
    def test_python_extract_blocks_function(self):
        """Test 3: Python extract.py blocks function test"""
        try:
            # Create test script with environment variable set
            test_script = '''
import os
import sys
# Set dummy OPENAI_API_KEY to avoid import error
os.environ['OPENAI_API_KEY'] = 'dummy-key-for-testing'
sys.path.insert(0, '/app/scripts')

try:
    from extract import convert_blocks_to_flat, normalize_column_name, COLUMN_ALIASES, validate_pass_1_raw
    
    # Test 1: blocks-to-flat conversion
    test_result = {
        'document_type': 'invoice',
        'blocks': [
            {'type': 'key_value', 'title': 'Company', 'data': {'Name': 'Test Corp', 'GSTIN': '27ABC123'}},
            {'type': 'table', 'title': 'Line Items', 'columns': ['Item', 'Qty', 'Rate', 'Amount'], 'rows': [
                {'Item': 'Widget', 'Qty': '10', 'Rate': '500', 'Amount': '5000'},
                {'Item': 'Gadget', 'Qty': '5', 'Rate': '1000', 'Amount': '5000'}
            ]}
        ]
    }
    result = convert_blocks_to_flat(test_result)
    assert result['columns'] == ['Item', 'Qty', 'Rate', 'Amount'], f"Expected table columns, got {result['columns']}"
    assert len(result['rows']) == 2, f"Expected 2 rows, got {len(result['rows'])}"
    assert result['blocks'] is not None, "blocks should be preserved"
    print("✅ blocks-to-flat conversion works")

    # Test 2: Column alias mapping
    assert normalize_column_name('txn date') == 'Date'
    assert normalize_column_name('narration') == 'Description'
    assert normalize_column_name('dr') == 'Debit'
    assert normalize_column_name('cr') == 'Credit'
    print("✅ Column aliases work")

    # Test 3: Validate blocks accepted by validation pass 1
    r, err = validate_pass_1_raw(test_result)
    assert err is None, f"Expected pass, got error: {err}"
    print("✅ Pass 1 accepts blocks format")
    
except ImportError as e:
    print(f"Import error: {e}")
    exit(1)
except Exception as e:
    print(f"Test error: {e}")
    exit(1)
'''
            
            result = subprocess.run(
                ["python3", "-c", test_script],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                output = result.stdout
                if "blocks-to-flat conversion works" in output and "Column aliases work" in output and "Pass 1 accepts blocks format" in output:
                    self.log_result("Python extract.py Blocks Function", True, "All block function tests passed")
                else:
                    self.log_result("Python extract.py Blocks Function", False, f"Some tests failed: {output}")
            else:
                error_output = result.stderr + result.stdout
                self.log_result("Python extract.py Blocks Function", False, f"Test script failed: {error_output}")
                
        except subprocess.TimeoutExpired:
            self.log_result("Python extract.py Blocks Function", False, "Test script timed out")
        except Exception as e:
            self.log_result("Python extract.py Blocks Function", False, f"Test failed: {str(e)}")
    
    def test_flexible_zod_schema(self):
        """Test 4: Flexible Zod schema — PUT /api/result/fake-uuid with body {"rows": [{"Name": "John"}], "columns": ["Name"]} — should return 401 (not 400)"""
        try:
            test_data = {
                "rows": [{"Name": "John"}],
                "columns": ["Name"]
            }
            
            response = self.session.put(f"{API_BASE}/result/fake-uuid", json=test_data)
            
            if response.status_code == 401:
                self.log_result("Flexible Zod Schema", True, "Returned 401 (auth required) instead of 400 (validation error) - schema accepts dynamic structure")
            elif response.status_code == 400:
                self.log_result("Flexible Zod Schema", False, f"Returned 400 (validation error) - schema may be too restrictive: {response.text}")
            else:
                self.log_result("Flexible Zod Schema", False, f"Unexpected status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Flexible Zod Schema", False, f"Request failed: {str(e)}")
    
    def test_cors_headers(self):
        """Test 5: CORS headers — OPTIONS /api/health — check Access-Control-Allow-Origin"""
        try:
            response = self.session.options(f"{API_BASE}/health")
            
            cors_header = response.headers.get('Access-Control-Allow-Origin')
            if cors_header:
                self.log_result("CORS Headers", True, f"Access-Control-Allow-Origin: {cors_header}")
            else:
                # Try GET request as fallback
                response = self.session.get(f"{API_BASE}/health")
                cors_header = response.headers.get('Access-Control-Allow-Origin')
                if cors_header:
                    self.log_result("CORS Headers", True, f"Access-Control-Allow-Origin (from GET): {cors_header}")
                else:
                    self.log_result("CORS Headers", False, "Missing Access-Control-Allow-Origin header")
                
        except Exception as e:
            self.log_result("CORS Headers", False, f"Request failed: {str(e)}")
    
    def test_geoip_api(self):
        """Test 6: GeoIP — GET /api/geo — verify returns country, currency, price fields"""
        try:
            response = self.session.get(f"{API_BASE}/geo")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['country', 'currency', 'price']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_result("GeoIP API", True, f"All required fields present: country={data.get('country')}, currency={data.get('currency')}, price={data.get('price')}")
                else:
                    self.log_result("GeoIP API", False, f"Missing required fields: {missing_fields}. Response: {data}")
            else:
                self.log_result("GeoIP API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("GeoIP API", False, f"Request failed: {str(e)}")
    
    def test_contact_validation(self):
        """Test 7: Contact validation — POST /api/contact with empty fields — should return 400"""
        try:
            # Test with completely empty body
            response = self.session.post(f"{API_BASE}/contact", json={})
            
            if response.status_code == 400:
                data = response.json()
                if "error" in data:
                    self.log_result("Contact Validation", True, f"Validation error for empty fields: {data['error']}")
                else:
                    self.log_result("Contact Validation", True, f"Returned 400 for empty fields: {data}")
            else:
                self.log_result("Contact Validation", False, f"Expected 400, got {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Contact Validation", False, f"Request failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests as specified in the review request"""
        print("🚀 Starting DocXL AI Backend Tests - Review Request")
        print("=" * 70)
        
        print("\n📡 Testing Core API Endpoints:")
        self.test_health_check_api()
        
        print("\n🐍 Testing Python Script Functionality:")
        self.test_python_extract_syntax()
        self.test_python_extract_blocks_function()
        
        print("\n🔧 Testing API Features:")
        self.test_flexible_zod_schema()
        self.test_cors_headers()
        self.test_geoip_api()
        self.test_contact_validation()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    
    if not success:
        print(f"\n⚠️  Some tests failed. Check the details above.")
        sys.exit(1)
    else:
        print(f"\n🎉 All tests passed!")
        sys.exit(0)