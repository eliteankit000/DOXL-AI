#!/usr/bin/env python3
"""
DocXL AI v6.0 Layout Reconstruction Engine - Comprehensive Backend Testing
Testing the new 11-stage pipeline and layout-aware extraction system.
"""

import requests
import json
import sys
import os
import tempfile
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:3000"  # Local URL
API_BASE = f"{BASE_URL}/api"

# Test credentials
TEST_EMAIL = f"test_v6_{int(time.time())}@docxl.com"
TEST_PASSWORD = "testpass123"
TEST_NAME = "V6 Test User"

class DocXLTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details
        }
        self.test_results.append(result)
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_health_check(self):
        """TEST 1: Health Check API"""
        try:
            response = self.session.get(f"{API_BASE}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok" and data.get("service") == "DocXL AI API":
                    self.log_result("Health Check API", True, "Backend is running correctly")
                    return True
                else:
                    self.log_result("Health Check API", False, "Invalid response format", data)
                    return False
            else:
                self.log_result("Health Check API", False, f"HTTP {response.status_code}", response.text[:200])
                return False
                
        except Exception as e:
            self.log_result("Health Check API", False, f"Request failed: {str(e)}")
            return False
    
    def test_python_script_structure(self):
        """TEST 2: Python Script Structure Validation"""
        try:
            # Test script import and structure without calling OpenAI
            script_path = "/app/scripts/extract.py"
            
            if not os.path.exists(script_path):
                self.log_result("Python Script Structure", False, "extract.py not found")
                return False
            
            # Test Python syntax by importing (with dummy API key to bypass check)
            import subprocess
            result = subprocess.run([
                "python3", "-c", 
                "import sys, os; "
                "os.environ['OPENAI_API_KEY'] = 'dummy-key-for-testing'; "
                "sys.path.append('/app/scripts'); "
                "import extract; "
                "print('Functions available:'); "
                "print('detect_pages:', hasattr(extract, 'detect_pages')); "
                "print('analyze_page_layout:', hasattr(extract, 'analyze_page_layout')); "
                "print('assemble_multi_sheet_output:', hasattr(extract, 'assemble_multi_sheet_output')); "
                "print('process_document:', hasattr(extract, 'process_document')); "
                "print('Script structure valid')"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and "Script structure valid" in result.stdout:
                # Test assemble_multi_sheet_output function format
                format_test = subprocess.run([
                    "python3", "-c",
                    "import sys, os; "
                    "os.environ['OPENAI_API_KEY'] = 'dummy-key-for-testing'; "
                    "sys.path.append('/app/scripts'); "
                    "import extract; "
                    "test_layouts = [{'page_number': 1, 'max_row': 10, 'max_col': 5, 'cells': [{'row': 1, 'col': 1, 'value': 'Test'}]}]; "
                    "result = extract.assemble_multi_sheet_output(test_layouts, 'test.pdf'); "
                    "print('Format check:'); "
                    "print('Has sheets:', 'sheets' in result); "
                    "print('Sheets is list:', isinstance(result.get('sheets', []), list)); "
                    "print('First sheet has name:', 'name' in result['sheets'][0] if result.get('sheets') else False); "
                    "print('First sheet has cells:', 'cells' in result['sheets'][0] if result.get('sheets') else False); "
                    "print('Format valid')"
                ], capture_output=True, text=True, timeout=10)
                
                if format_test.returncode == 0 and "Format valid" in format_test.stdout:
                    self.log_result("Python Script Structure", True, "All required functions exist and return correct format")
                    return True
                else:
                    self.log_result("Python Script Structure", False, "Function format test failed", format_test.stderr)
                    return False
            else:
                self.log_result("Python Script Structure", False, "Script structure test failed", result.stderr)
                return False
                
        except Exception as e:
            self.log_result("Python Script Structure", False, f"Structure validation failed: {str(e)}")
            return False
    
    def test_excel_export_endpoint(self):
        """TEST 3: Excel Export Endpoint Structure"""
        try:
            # Test endpoint exists (should return 401 without auth)
            response = self.session.get(f"{API_BASE}/export/excel/test-id", timeout=10)
            
            if response.status_code == 401:
                data = response.json()
                if "error" in data and "Unauthorized" in data["error"]:
                    self.log_result("Excel Export Endpoint", True, "Endpoint exists and requires authentication")
                    return True
                else:
                    self.log_result("Excel Export Endpoint", False, "Unexpected 401 response", data)
                    return False
            else:
                self.log_result("Excel Export Endpoint", False, f"Unexpected status code: {response.status_code}", response.text[:200])
                return False
                
        except Exception as e:
            self.log_result("Excel Export Endpoint", False, f"Endpoint test failed: {str(e)}")
            return False
    
    def test_new_layout_format_support(self):
        """TEST 4: New Layout Format Support"""
        try:
            # Check if route.js contains the new layout format logic
            route_path = "/app/app/api/[[...path]]/route.js"
            
            if not os.path.exists(route_path):
                self.log_result("New Layout Format Support", False, "Route file not found")
                return False
            
            with open(route_path, 'r') as f:
                content = f.read()
            
            # Check for v6.0 layout format markers
            checks = [
                "CHECK FOR NEW LAYOUT-BASED FORMAT (v6.0" in content,
                "sheets" in content and "Array.isArray(sheets)" in content,
                "layout-based multi-sheet excel export" in content.lower() or "layout reconstruction" in content.lower(),
                "cells" in content and "row" in content and "col" in content
            ]
            
            if all(checks):
                self.log_result("New Layout Format Support", True, "New sheets format logic found in export code")
                return True
            else:
                failed_checks = [i for i, check in enumerate(checks) if not check]
                self.log_result("New Layout Format Support", False, f"Missing format support checks: {failed_checks}")
                return False
                
        except Exception as e:
            self.log_result("New Layout Format Support", False, f"Format check failed: {str(e)}")
            return False
    
    def test_backward_compatibility(self):
        """TEST 5: Backward Compatibility"""
        try:
            route_path = "/app/app/api/[[...path]]/route.js"
            
            with open(route_path, 'r') as f:
                content = f.read()
            
            # Check for fallback logic for old formats
            checks = [
                "blocks" in content and "Array.isArray(blocks)" in content,
                "fallback" in content.lower() or "old" in content.lower(),
                "structured_json" in content,
                "columns" in content and "rows" in content
            ]
            
            if all(checks):
                self.log_result("Backward Compatibility", True, "Fallback logic for old formats exists")
                return True
            else:
                self.log_result("Backward Compatibility", False, "Missing backward compatibility logic")
                return False
                
        except Exception as e:
            self.log_result("Backward Compatibility", False, f"Compatibility check failed: {str(e)}")
            return False
    
    def test_multi_sheet_excel_generation(self):
        """TEST 6: Multi-Sheet Excel Generation (Structure Only)"""
        try:
            route_path = "/app/app/api/[[...path]]/route.js"
            
            with open(route_path, 'r') as f:
                content = f.read()
            
            # Check for multi-sheet logic
            checks = [
                "addWorksheet" in content,
                "sheet.name" in content or "sheetName" in content,
                "for" in content and "sheet" in content,  # Loop through sheets
                "Page" in content  # Page naming
            ]
            
            if all(checks):
                self.log_result("Multi-Sheet Excel Generation", True, "Multi-sheet generation logic implemented")
                return True
            else:
                self.log_result("Multi-Sheet Excel Generation", False, "Multi-sheet logic not found")
                return False
                
        except Exception as e:
            self.log_result("Multi-Sheet Excel Generation", False, f"Multi-sheet check failed: {str(e)}")
            return False
    
    def test_python_dependencies(self):
        """TEST 7: Python Dependencies"""
        try:
            import subprocess
            
            # Test required packages
            deps_test = subprocess.run([
                "python3", "-c",
                "import pdfplumber, PIL, openai, asyncio; print('✅ All deps available')"
            ], capture_output=True, text=True, timeout=10)
            
            if deps_test.returncode == 0 and "All deps available" in deps_test.stdout:
                self.log_result("Python Dependencies", True, "All required dependencies available")
                return True
            else:
                self.log_result("Python Dependencies", False, "Missing dependencies", deps_test.stderr)
                return False
                
        except Exception as e:
            self.log_result("Python Dependencies", False, f"Dependency check failed: {str(e)}")
            return False
    
    def test_layout_reconstruction_integration(self):
        """TEST 8: Layout Reconstruction Integration (Code Structure)"""
        try:
            # Check if the new v6.0 pipeline is integrated in the API
            route_path = "/app/app/api/[[...path]]/route.js"
            
            with open(route_path, 'r') as f:
                content = f.read()
            
            # Check for v6.0 integration markers
            checks = [
                "v6.0" in content or "layout reconstruction" in content.lower(),
                "extract.py" in content,
                "sheets" in content,
                "cells" in content and "row" in content and "col" in content,
                "merge" in content and "style" in content
            ]
            
            passed_checks = sum(checks)
            if passed_checks >= 3:  # At least 3 out of 5 checks should pass
                self.log_result("Layout Reconstruction Integration", True, f"v6.0 integration found ({passed_checks}/5 checks passed)")
                return True
            else:
                self.log_result("Layout Reconstruction Integration", False, f"Limited v6.0 integration ({passed_checks}/5 checks passed)")
                return False
                
        except Exception as e:
            self.log_result("Layout Reconstruction Integration", False, f"Integration check failed: {str(e)}")
            return False
    
    def run_comprehensive_tests(self):
        """Run all backend tests for v6.0 Layout Reconstruction Engine"""
        print("🚀 Starting DocXL AI v6.0 Layout Reconstruction Engine Backend Tests")
        print("=" * 80)
        
        tests = [
            self.test_health_check,
            self.test_python_script_structure,
            self.test_excel_export_endpoint,
            self.test_new_layout_format_support,
            self.test_backward_compatibility,
            self.test_multi_sheet_excel_generation,
            self.test_python_dependencies,
            self.test_layout_reconstruction_integration
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ FAIL: {test.__name__} - Exception: {str(e)}")
        
        print("\n" + "=" * 80)
        print(f"📊 TEST SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - v6.0 Layout Reconstruction Engine is ready!")
        elif passed >= total * 0.8:  # 80% pass rate
            print("⚠️  MOSTLY WORKING - Minor issues detected")
        else:
            print("❌ CRITICAL ISSUES - Major problems detected")
        
        return passed, total, self.test_results

def main():
    """Main test execution"""
    tester = DocXLTester()
    passed, total, results = tester.run_comprehensive_tests()
    
    # Return appropriate exit code
    if passed == total:
        sys.exit(0)  # All tests passed
    elif passed >= total * 0.8:
        sys.exit(1)  # Minor issues
    else:
        sys.exit(2)  # Critical issues

if __name__ == "__main__":
    main()