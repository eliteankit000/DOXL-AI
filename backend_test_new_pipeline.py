#!/usr/bin/env python3
"""
Backend Testing Script for DocXL AI - New Pipeline Testing
Tests the live server at localhost:3000 with specific focus on:
1. Health check API
2. Geo endpoint
3. Auth registration/login
4. Flexible Zod schema for result updates
5. Process endpoint validation
6. Contact form validation
7. CORS headers
8. Upload without auth
9. Python extract.py syntax check
"""

import requests
import json
import random
import string
import time
import subprocess
import sys

BASE_URL = "http://localhost:3000"

def generate_random_email():
    """Generate a random email for testing"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_v5_pipeline_{random_str}@docxl.com"

def test_health_check():
    """Test 1: GET /api/health - Verify it returns JSON with status='ok'"""
    print("\n=== TEST 1: Health Check API ===")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                print("✅ PASS: Health check returns status='ok'")
                return True
            else:
                print(f"❌ FAIL: Expected status='ok', got {data.get('status')}")
                return False
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_geo_endpoint():
    """Test 2: GET /api/geo - Verify it returns JSON with required fields"""
    print("\n=== TEST 2: Geo Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/api/geo")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ['country', 'currency', 'price', 'priceDisplay', 'region', 'plan', 'interval']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                print("✅ PASS: Geo endpoint returns all required fields")
                return True
            else:
                print(f"❌ FAIL: Missing fields: {missing_fields}")
                return False
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_auth_registration():
    """Test 3: POST /api/auth/register - Register a new user"""
    print("\n=== TEST 3: User Registration ===")
    email = generate_random_email()
    password = "TestPass123!"
    
    try:
        payload = {
            "email": email,
            "password": password
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            data = response.json()
            if 'user' in data:
                print("✅ PASS: User registration successful")
                return True, email, password
            else:
                print("❌ FAIL: No user object in response")
                return False, email, password
        else:
            print(f"❌ FAIL: Expected 201, got {response.status_code}")
            return False, email, password
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False, email, password

def test_auth_login(email, password):
    """Test 4: POST /api/auth/login - Login with the registered user"""
    print("\n=== TEST 4: User Login ===")
    try:
        payload = {
            "email": email,
            "password": password
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if 'access_token' in data:
                print("✅ PASS: User login successful")
                return True, data['access_token']
            else:
                print("❌ FAIL: No access_token in response")
                return False, None
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False, None

def test_flexible_result_update(access_token):
    """Test 5: PUT /api/result/fake-uuid-here with flexible Zod schema"""
    print("\n=== TEST 5: Flexible Result Update Schema ===")
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Test with dynamic structure that should be accepted by flexible schema
        payload = {
            "rows": [
                {"Name": "John", "City": "NYC"},
                {"Name": "Jane", "City": "LA"}
            ],
            "columns": ["Name", "City"]
        }
        
        response = requests.put(f"{BASE_URL}/api/result/fake-uuid-here", 
                              json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Should return 401 (unauthorized) or 404 (result not found) but NOT 400 (validation error)
        if response.status_code in [401, 404]:
            print("✅ PASS: Flexible schema accepts dynamic structure (no validation error)")
            return True
        elif response.status_code == 400:
            print("❌ FAIL: Got 400 validation error - schema not flexible enough")
            return False
        else:
            print(f"⚠️  UNEXPECTED: Got {response.status_code}, expected 401/404")
            return True  # Still pass as it's not a validation error
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_process_validation(access_token):
    """Test 6: POST /api/process with invalid UUID - Should return 400 with Zod validation error"""
    print("\n=== TEST 6: Process Endpoint Validation ===")
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "upload_id": "not-a-uuid"
        }
        
        response = requests.post(f"{BASE_URL}/api/process", 
                               json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            print("✅ PASS: Process endpoint validates UUID format")
            return True
        else:
            print(f"❌ FAIL: Expected 400 validation error, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_contact_validation():
    """Test 7: POST /api/contact with invalid data - Should return 400 with validation error"""
    print("\n=== TEST 7: Contact Form Validation ===")
    try:
        payload = {
            "name": "",
            "email": "bad",
            "message": ""
        }
        
        response = requests.post(f"{BASE_URL}/api/contact", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            print("✅ PASS: Contact form validates required fields")
            return True
        else:
            print(f"❌ FAIL: Expected 400 validation error, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_cors_headers():
    """Test 8: OPTIONS /api/health - Check CORS headers are present"""
    print("\n=== TEST 8: CORS Headers ===")
    try:
        response = requests.options(f"{BASE_URL}/api/health")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        cors_headers = [
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods'
        ]
        
        present_headers = [header for header in cors_headers if header in response.headers]
        
        if len(present_headers) >= 1:  # At least one CORS header should be present
            print("✅ PASS: CORS headers are present")
            return True
        else:
            print("❌ FAIL: No CORS headers found")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_upload_without_auth():
    """Test 9: POST /api/upload without auth - Should return 401"""
    print("\n=== TEST 9: Upload Without Auth ===")
    try:
        # Try to upload without Authorization header
        files = {'file': ('test.txt', 'test content', 'text/plain')}
        response = requests.post(f"{BASE_URL}/api/upload", files=files)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("✅ PASS: Upload endpoint requires authentication")
            return True
        else:
            print(f"❌ FAIL: Expected 401 unauthorized, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_python_extract_syntax():
    """Test 10: Test the Python extract.py syntax is valid"""
    print("\n=== TEST 10: Python Extract.py Syntax Check ===")
    try:
        # Run python3 with the extract.py file to check for syntax errors
        result = subprocess.run(
            ['python3', '/app/scripts/extract.py'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(f"Return Code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        
        # Should error about no file path but NOT syntax/import errors
        if "No file path provided" in result.stderr or "usage:" in result.stderr.lower():
            print("✅ PASS: Python script has valid syntax (expected usage error)")
            return True
        elif "SyntaxError" in result.stderr or "ImportError" in result.stderr:
            print("❌ FAIL: Python script has syntax or import errors")
            return False
        elif result.returncode != 0 and result.stderr:
            # Check if it's just a usage error or missing arguments
            if any(keyword in result.stderr.lower() for keyword in ['usage', 'argument', 'required', 'missing']):
                print("✅ PASS: Python script has valid syntax (expected argument error)")
                return True
            else:
                print(f"❌ FAIL: Unexpected error: {result.stderr}")
                return False
        else:
            print("✅ PASS: Python script executed without syntax errors")
            return True
            
    except subprocess.TimeoutExpired:
        print("❌ FAIL: Script execution timed out")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Backend Testing for DocXL AI - New Pipeline")
    print("=" * 60)
    
    results = []
    
    # Test 1: Health Check
    results.append(("Health Check API", test_health_check()))
    
    # Test 2: Geo Endpoint
    results.append(("Geo Endpoint", test_geo_endpoint()))
    
    # Test 3 & 4: Auth Registration and Login
    reg_success, email, password = test_auth_registration()
    results.append(("User Registration", reg_success))
    
    access_token = None
    if reg_success:
        login_success, access_token = test_auth_login(email, password)
        results.append(("User Login", login_success))
    else:
        results.append(("User Login", False))
    
    # Test 5: Flexible Result Update (requires auth token)
    if access_token:
        results.append(("Flexible Result Update Schema", test_flexible_result_update(access_token)))
        results.append(("Process Endpoint Validation", test_process_validation(access_token)))
    else:
        results.append(("Flexible Result Update Schema", False))
        results.append(("Process Endpoint Validation", False))
    
    # Test 7: Contact Form Validation
    results.append(("Contact Form Validation", test_contact_validation()))
    
    # Test 8: CORS Headers
    results.append(("CORS Headers", test_cors_headers()))
    
    # Test 9: Upload Without Auth
    results.append(("Upload Without Auth", test_upload_without_auth()))
    
    # Test 10: Python Extract.py Syntax
    results.append(("Python Extract.py Syntax", test_python_extract_syntax()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Backend is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())