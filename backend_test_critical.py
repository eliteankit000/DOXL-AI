#!/usr/bin/env python3
"""
DocXL AI Backend Testing Script - Critical New Endpoints Only
Focused test for the NEW endpoints added in v3.0 update.
"""

import requests
import json
import time
import sys

# Base URL for testing
BASE_URL = "http://localhost:3000"
API_BASE = f"{BASE_URL}/api"

def test_health_check():
    """Test GET /api/health endpoint"""
    print("Testing Health Check...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok" and data.get("backend") == "supabase":
                print("✅ Health Check: PASS - Status: ok, Backend: supabase")
                return True
            else:
                print(f"❌ Health Check: FAIL - Unexpected response: {data}")
                return False
        else:
            print(f"❌ Health Check: FAIL - HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Health Check: FAIL - Request failed: {str(e)}")
        return False

def test_contact_form():
    """Test POST /api/contact endpoint"""
    print("Testing Contact Form...")
    
    # Test 1: Missing fields (should return 400)
    try:
        response = requests.post(f"{API_BASE}/contact", json={}, timeout=10)
        
        if response.status_code == 400:
            data = response.json()
            if "error" in data:
                print("✅ Contact Form Validation: PASS - Correctly rejects missing fields")
            else:
                print(f"❌ Contact Form Validation: FAIL - Missing error field: {data}")
                return False
        else:
            print(f"❌ Contact Form Validation: FAIL - Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Contact Form Validation: FAIL - Request failed: {str(e)}")
        return False
    
    # Test 2: Valid data (should return 500 due to missing BREVO_API_KEY)
    try:
        valid_data = {
            "name": "Test User",
            "email": "test@example.com", 
            "message": "Test message"
        }
        
        response = requests.post(f"{API_BASE}/contact", json=valid_data, timeout=10)
        
        if response.status_code == 500:
            data = response.json()
            if "error" in data and ("BREVO_API_KEY" in data["error"] or "Failed to send message" in data["error"]):
                print("✅ Contact Form Valid Data: PASS - Expected BREVO error")
                return True
            else:
                print(f"❌ Contact Form Valid Data: FAIL - Unexpected error: {data}")
                return False
        else:
            print(f"❌ Contact Form Valid Data: FAIL - Expected 500, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Contact Form Valid Data: FAIL - Request failed: {str(e)}")
        return False

def test_forgot_password():
    """Test POST /api/auth/forgot-password endpoint"""
    print("Testing Forgot Password...")
    
    # Test 1: Missing email (should return 400)
    try:
        response = requests.post(f"{API_BASE}/auth/forgot-password", json={}, timeout=10)
        
        if response.status_code == 400:
            data = response.json()
            if "error" in data:
                print("✅ Forgot Password Validation: PASS - Correctly rejects missing email")
            else:
                print(f"❌ Forgot Password Validation: FAIL - Missing error field: {data}")
                return False
        else:
            print(f"❌ Forgot Password Validation: FAIL - Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Forgot Password Validation: FAIL - Request failed: {str(e)}")
        return False
    
    # Test 2: Valid email (should always return 200 with success=true)
    try:
        valid_data = {"email": "test@example.com"}
        
        response = requests.post(f"{API_BASE}/auth/forgot-password", json=valid_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") is True:
                print("✅ Forgot Password Valid Email: PASS - Returns success=true")
                return True
            else:
                print(f"❌ Forgot Password Valid Email: FAIL - Expected success=true: {data}")
                return False
        else:
            print(f"❌ Forgot Password Valid Email: FAIL - Expected 200, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Forgot Password Valid Email: FAIL - Request failed: {str(e)}")
        return False

def test_admin_endpoints():
    """Test admin endpoints without authentication (should return 401/403)"""
    print("Testing Admin Endpoints...")
    
    admin_tests = [
        ("GET", "/admin/users"),
        ("POST", "/admin/credits", {"userId": "test", "newCredits": 100}),
        ("GET", "/admin/stats"),
        ("GET", "/admin/activity"),
        ("GET", "/admin/search?email=test")
    ]
    
    all_passed = True
    
    for method, endpoint, *payload in admin_tests:
        try:
            if method == "GET":
                response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
            elif method == "POST":
                response = requests.post(f"{API_BASE}{endpoint}", json=payload[0] if payload else {}, timeout=10)
            
            if response.status_code in [401, 403]:
                print(f"✅ Admin {method} {endpoint}: PASS - Correctly unauthorized ({response.status_code})")
            else:
                print(f"❌ Admin {method} {endpoint}: FAIL - Expected 401/403, got {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Admin {method} {endpoint}: FAIL - Request failed: {str(e)}")
            all_passed = False
    
    return all_passed

def test_cors_headers():
    """Test CORS headers are present"""
    print("Testing CORS Headers...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        
        cors_header = response.headers.get('Access-Control-Allow-Origin')
        if cors_header:
            print(f"✅ CORS Headers: PASS - Access-Control-Allow-Origin: {cors_header}")
            return True
        else:
            print("❌ CORS Headers: FAIL - Missing Access-Control-Allow-Origin header")
            return False
            
    except Exception as e:
        print(f"❌ CORS Headers: FAIL - Request failed: {str(e)}")
        return False

def test_static_content():
    """Test sitemap and robots.txt"""
    print("Testing Static Content...")
    
    # Test sitemap.xml
    try:
        response = requests.get(f"{BASE_URL}/sitemap.xml", timeout=10)
        
        if response.status_code == 200:
            content = response.text
            if "<?xml" in content and "https://docxl.ai" in content:
                url_count = content.count("<url>")
                print(f"✅ Sitemap XML: PASS - Valid XML with {url_count} URLs")
                sitemap_ok = True
            else:
                print("❌ Sitemap XML: FAIL - Invalid XML format")
                sitemap_ok = False
        else:
            print(f"❌ Sitemap XML: FAIL - HTTP {response.status_code}")
            sitemap_ok = False
            
    except Exception as e:
        print(f"❌ Sitemap XML: FAIL - Request failed: {str(e)}")
        sitemap_ok = False
    
    # Test robots.txt
    try:
        response = requests.get(f"{BASE_URL}/robots.txt", timeout=10)
        
        if response.status_code == 200:
            content = response.text
            if "Disallow: /admin" in content and "Disallow: /api/" in content:
                print("✅ Robots.txt: PASS - Contains expected disallow rules")
                robots_ok = True
            else:
                print("❌ Robots.txt: FAIL - Missing expected disallow rules")
                robots_ok = False
        else:
            print(f"❌ Robots.txt: FAIL - HTTP {response.status_code}")
            robots_ok = False
            
    except Exception as e:
        print(f"❌ Robots.txt: FAIL - Request failed: {str(e)}")
        robots_ok = False
    
    return sitemap_ok and robots_ok

def main():
    """Run all critical backend tests"""
    print("🚀 DocXL AI Backend Tests - Critical New Endpoints")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health_check),
        ("Contact Form", test_contact_form),
        ("Forgot Password", test_forgot_password),
        ("Admin Endpoints", test_admin_endpoints),
        ("CORS Headers", test_cors_headers),
        ("Static Content", test_static_content),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📡 {test_name}:")
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All critical backend tests passed!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)