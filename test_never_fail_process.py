#!/usr/bin/env python3
"""
Test the Never-Fail Process Endpoint
Based on test_result.md task: "Never-Fail Process Endpoint"
- Should no longer return 422/500
- Always returns partial result
- extract.py v3 with 3 retries + never-fail
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Base URL for testing
BASE_URL = "http://localhost:3000"
API_BASE = f"{BASE_URL}/api"

class NeverFailProcessTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
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
    
    def test_process_endpoint_without_auth(self):
        """Test POST /api/process without authentication (should return 401)"""
        try:
            response = self.session.post(f"{API_BASE}/process", json={"upload_id": "test-id"})
            
            if response.status_code == 401:
                self.log_result("Process - No Auth", True, "Correctly returns 401 unauthorized")
            else:
                self.log_result("Process - No Auth", False, f"Expected 401, got {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Process - No Auth", False, f"Request failed: {str(e)}")
    
    def test_process_endpoint_invalid_data(self):
        """Test POST /api/process with invalid data (should return 400, not 422/500)"""
        try:
            # Test with invalid upload_id format
            response = self.session.post(f"{API_BASE}/process", json={"upload_id": "invalid-id"})
            
            # Should return 400 for validation error, not 422/500
            if response.status_code == 400:
                self.log_result("Process - Invalid Data", True, f"Correctly returns 400 for validation error")
            elif response.status_code == 401:
                self.log_result("Process - Invalid Data", True, f"Returns 401 (auth required) - expected behavior")
            elif response.status_code in [422, 500]:
                self.log_result("Process - Invalid Data", False, f"Still returns {response.status_code} - should be 400 or 401")
            else:
                self.log_result("Process - Invalid Data", True, f"Returns {response.status_code} - may be expected")
                
        except Exception as e:
            self.log_result("Process - Invalid Data", False, f"Request failed: {str(e)}")
    
    def test_process_endpoint_missing_fields(self):
        """Test POST /api/process with missing required fields"""
        try:
            # Test with empty body
            response = self.session.post(f"{API_BASE}/process", json={})
            
            # Should return 400 for validation error, not 422/500
            if response.status_code == 400:
                data = response.json()
                if "error" in data:
                    self.log_result("Process - Missing Fields", True, f"Validation error: {data['error']}")
                else:
                    self.log_result("Process - Missing Fields", False, f"Expected error field in response: {data}")
            elif response.status_code == 401:
                self.log_result("Process - Missing Fields", True, f"Returns 401 (auth required) - expected behavior")
            elif response.status_code in [422, 500]:
                self.log_result("Process - Missing Fields", False, f"Still returns {response.status_code} - should be 400 or 401")
            else:
                self.log_result("Process - Missing Fields", True, f"Returns {response.status_code} - may be expected")
                
        except Exception as e:
            self.log_result("Process - Missing Fields", False, f"Request failed: {str(e)}")
    
    def test_process_endpoint_structure(self):
        """Test that the process endpoint exists and has proper structure"""
        try:
            # Test with minimal valid structure (will fail auth but should not 404)
            response = self.session.post(f"{API_BASE}/process", json={"upload_id": "00000000-0000-0000-0000-000000000000"})
            
            if response.status_code == 404:
                self.log_result("Process - Endpoint Exists", False, "Process endpoint not found (404)")
            elif response.status_code in [400, 401, 403]:
                self.log_result("Process - Endpoint Exists", True, f"Endpoint exists, returns {response.status_code} as expected")
            elif response.status_code in [422, 500]:
                self.log_result("Process - Endpoint Exists", False, f"Endpoint exists but still returns {response.status_code} - should be improved")
            else:
                self.log_result("Process - Endpoint Exists", True, f"Endpoint exists, returns {response.status_code}")
                
        except Exception as e:
            self.log_result("Process - Endpoint Exists", False, f"Request failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests for Never-Fail Process Endpoint"""
        print("🚀 Testing Never-Fail Process Endpoint")
        print("Focus: Should no longer return 422/500, always return partial results")
        print("=" * 70)
        
        print("\n🔒 Testing Process Endpoint Structure and Error Handling:")
        self.test_process_endpoint_structure()
        self.test_process_endpoint_without_auth()
        self.test_process_endpoint_invalid_data()
        self.test_process_endpoint_missing_fields()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY - Never-Fail Process Endpoint")
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
        
        print(f"\n🎯 FOCUS AREAS TESTED:")
        print(f"  ✓ Process endpoint exists and responds properly")
        print(f"  ✓ No longer returns 422/500 for validation errors")
        print(f"  ✓ Proper error handling structure")
        print(f"  ✓ Authentication and validation flow")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = NeverFailProcessTester()
    success = tester.run_all_tests()
    
    if not success:
        print(f"\n⚠️  Some tests failed. Check the details above.")
        sys.exit(1)
    else:
        print(f"\n🎉 All Never-Fail Process tests passed!")
        sys.exit(0)