#!/usr/bin/env python3
"""
DocXL AI Backend Testing Script - v3.0 New Endpoints Focus
Tests the NEW endpoints added in the latest update.
"""

import requests
import json
import time
import sys
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
    
    def test_health_check(self):
        """Test GET /api/health endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/health")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok" and data.get("backend") == "supabase":
                    self.log_result("Health Check", True, f"Status: {data.get('status')}, Backend: {data.get('backend')}")
                else:
                    self.log_result("Health Check", False, f"Unexpected response format: {data}")
            else:
                self.log_result("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Health Check", False, f"Request failed: {str(e)}")
    
    def test_contact_form_validation(self):
        """Test POST /api/contact validation"""
        try:
            # Test missing fields
            response = self.session.post(f"{API_BASE}/contact", json={})
            
            if response.status_code == 400:
                data = response.json()
                if "error" in data:
                    self.log_result("Contact Form - Missing Fields", True, f"Validation error: {data['error']}")
                else:
                    self.log_result("Contact Form - Missing Fields", False, f"Expected error field in response: {data}")
            else:
                self.log_result("Contact Form - Missing Fields", False, f"Expected 400, got {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Contact Form - Missing Fields", False, f"Request failed: {str(e)}")
    
    def test_contact_form_valid_data(self):
        """Test POST /api/contact with valid data (should fail due to missing BREVO_API_KEY)"""
        try:
            valid_data = {
                "name": "Test User",
                "email": "test@example.com", 
                "message": "This is a test message from the backend testing script."
            }
            
            response = self.session.post(f"{API_BASE}/contact", json=valid_data)
            
            # Should return 500 due to missing BREVO_API_KEY (this is expected)
            if response.status_code == 500:
                data = response.json()
                if "error" in data and "BREVO_API_KEY" in data["error"]:
                    self.log_result("Contact Form - Valid Data", True, f"Expected BREVO error: {data['error']}")
                else:
                    self.log_result("Contact Form - Valid Data", True, f"Got 500 error as expected: {data.get('error', 'Unknown error')}")
            else:
                self.log_result("Contact Form - Valid Data", False, f"Expected 500, got {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Contact Form - Valid Data", False, f"Request failed: {str(e)}")
    
    def test_forgot_password_validation(self):
        """Test POST /api/auth/forgot-password validation"""
        try:
            # Test missing email
            response = self.session.post(f"{API_BASE}/auth/forgot-password", json={})
            
            if response.status_code == 400:
                data = response.json()
                if "error" in data:
                    self.log_result("Forgot Password - Missing Email", True, f"Validation error: {data['error']}")
                else:
                    self.log_result("Forgot Password - Missing Email", False, f"Expected error field: {data}")
            else:
                self.log_result("Forgot Password - Missing Email", False, f"Expected 400, got {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Forgot Password - Missing Email", False, f"Request failed: {str(e)}")
    
    def test_forgot_password_valid_email(self):
        """Test POST /api/auth/forgot-password with valid email (should always return 200)"""
        try:
            valid_data = {"email": "test@example.com"}
            
            response = self.session.post(f"{API_BASE}/auth/forgot-password", json=valid_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") is True:
                    self.log_result("Forgot Password - Valid Email", True, f"Success response: {data.get('message', 'No message')}")
                else:
                    self.log_result("Forgot Password - Valid Email", False, f"Expected success=true: {data}")
            else:
                self.log_result("Forgot Password - Valid Email", False, f"Expected 200, got {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Forgot Password - Valid Email", False, f"Request failed: {str(e)}")
    
    def test_admin_endpoints_unauthorized(self):
        """Test admin endpoints without authentication (should return 401/403)"""
        admin_endpoints = [
            ("GET", "/admin/users"),
            ("POST", "/admin/credits"),
            ("GET", "/admin/stats"),
            ("GET", "/admin/activity"),
            ("GET", "/admin/search?email=test")
        ]
        
        for method, endpoint in admin_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{API_BASE}{endpoint}")
                elif method == "POST":
                    response = self.session.post(f"{API_BASE}{endpoint}", json={"userId": "test", "newCredits": 100})
                
                if response.status_code in [401, 403]:
                    self.log_result(f"Admin {method} {endpoint}", True, f"Correctly unauthorized: {response.status_code}")
                else:
                    self.log_result(f"Admin {method} {endpoint}", False, f"Expected 401/403, got {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_result(f"Admin {method} {endpoint}", False, f"Request failed: {str(e)}")
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        try:
            response = self.session.get(f"{API_BASE}/health")
            
            cors_header = response.headers.get('Access-Control-Allow-Origin')
            if cors_header:
                self.log_result("CORS Headers", True, f"Access-Control-Allow-Origin: {cors_header}")
            else:
                self.log_result("CORS Headers", False, "Missing Access-Control-Allow-Origin header")
                
        except Exception as e:
            self.log_result("CORS Headers", False, f"Request failed: {str(e)}")
    
    def test_sitemap_xml(self):
        """Test GET /sitemap.xml"""
        try:
            response = self.session.get(f"{BASE_URL}/sitemap.xml")
            
            if response.status_code == 200:
                content = response.text
                # Check if it's valid XML and contains expected URLs
                if "<?xml" in content and "https://docxl.ai" in content:
                    # Count URLs in sitemap
                    url_count = content.count("<url>")
                    self.log_result("Sitemap XML", True, f"Valid XML with {url_count} URLs")
                else:
                    self.log_result("Sitemap XML", False, f"Invalid XML format or missing URLs")
            else:
                self.log_result("Sitemap XML", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Sitemap XML", False, f"Request failed: {str(e)}")
    
    def test_robots_txt(self):
        """Test GET /robots.txt"""
        try:
            response = self.session.get(f"{BASE_URL}/robots.txt")
            
            if response.status_code == 200:
                content = response.text
                if "Disallow: /admin" in content and "Disallow: /api/" in content:
                    self.log_result("Robots.txt", True, "Contains expected disallow rules")
                else:
                    self.log_result("Robots.txt", False, f"Missing expected disallow rules: {content}")
            else:
                self.log_result("Robots.txt", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Robots.txt", False, f"Request failed: {str(e)}")
    
    def test_static_assets(self):
        """Test static assets return 200"""
        assets = [
            "/favicon.ico",
            "/og-image.png", 
            "/site.webmanifest",
            "/icon-192.png"
        ]
        
        for asset in assets:
            try:
                response = self.session.get(f"{BASE_URL}{asset}")
                
                if response.status_code == 200:
                    self.log_result(f"Static Asset {asset}", True, f"Size: {len(response.content)} bytes")
                else:
                    self.log_result(f"Static Asset {asset}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Static Asset {asset}", False, f"Request failed: {str(e)}")
    
    def test_page_routes(self):
        """Test page routes return 200"""
        pages = [
            "/pricing",
            "/blog", 
            "/blog/convert-pdf-to-excel",
            "/blog/invoice-to-excel",
            "/blog/bank-statement-to-excel",
            "/contact",
            "/terms",
            "/privacy"
        ]
        
        for page in pages:
            try:
                response = self.session.get(f"{BASE_URL}{page}")
                
                if response.status_code == 200:
                    self.log_result(f"Page Route {page}", True, f"Content length: {len(response.content)}")
                else:
                    self.log_result(f"Page Route {page}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Page Route {page}", False, f"Request failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting DocXL AI Backend Tests - v3.0 New Endpoints Focus")
        print("=" * 70)
        
        # Test new API endpoints
        print("\n📡 Testing NEW API Endpoints:")
        self.test_health_check()
        self.test_contact_form_validation()
        self.test_contact_form_valid_data()
        self.test_forgot_password_validation()
        self.test_forgot_password_valid_email()
        
        print("\n🔒 Testing Admin Endpoints (Unauthorized):")
        self.test_admin_endpoints_unauthorized()
        
        print("\n🌐 Testing CORS and Static Content:")
        self.test_cors_headers()
        self.test_sitemap_xml()
        self.test_robots_txt()
        
        print("\n📁 Testing Static Assets:")
        self.test_static_assets()
        
        print("\n📄 Testing Page Routes:")
        self.test_page_routes()
        
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