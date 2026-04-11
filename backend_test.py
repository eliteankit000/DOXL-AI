#!/usr/bin/env python3
"""
DocXL AI Backend Testing Script
Tests the backend API after major extraction pipeline rewrite.

Key areas to test:
1. Python Extraction Pipeline (extract_and_build function)
2. Health Check API
3. Auth Flow (Register + Login)
4. File Size Limit (50MB)
5. Upload + Process Flow
6. Excel Export (pre-generated xlsx serving)
"""

import requests
import json
import sys
import os
import time
import tempfile
from io import BytesIO

# Backend URL from environment
BASE_URL = "http://localhost:3000"
API_BASE = f"{BASE_URL}/api"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 30
        # Disable SSL verification and add headers
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'DocXL-Backend-Tester/1.0',
            'Connection': 'close'
        })
        self.auth_token = None
        self.test_user_email = f"test_{int(time.time())}@docxl.com"
        self.test_user_password = "testpass123"
        self.upload_id = None
        self.result_id = None
        
    def log(self, message):
        print(f"[TEST] {message}")
        
    def test_python_imports(self):
        """Test 1: Python Extraction Pipeline - Import Test"""
        try:
            self.log("Testing Python imports...")
            
            # Test import of extract_and_build function
            import sys
            sys.path.insert(0, '/app')
            from lib.pdf_engine.extractor import extract_and_build, get_extraction_summary
            
            self.log("✅ Python imports successful - extract_and_build and get_extraction_summary functions available")
            return True
            
        except Exception as e:
            self.log(f"❌ Python import failed: {str(e)}")
            return False
    
    def test_python_script_execution(self):
        """Test 2: Python Script Execution Test"""
        try:
            self.log("Testing Python script execution...")
            
            # Test the extract.py script with invalid file (should handle gracefully)
            import subprocess
            result = subprocess.run([
                'python3', '/app/scripts/extract.py', '/dev/null'
            ], capture_output=True, text=True, timeout=30)
            
            # Should output JSON even for invalid file
            if result.stdout:
                try:
                    output = json.loads(result.stdout)
                    if 'error' in output:
                        self.log("✅ Python script handles invalid files gracefully with JSON error output")
                        return True
                except json.JSONDecodeError:
                    pass
            
            self.log(f"❌ Python script execution failed or invalid output")
            self.log(f"stdout: {result.stdout[:200]}")
            self.log(f"stderr: {result.stderr[:200]}")
            return False
            
        except Exception as e:
            self.log(f"❌ Python script execution test failed: {str(e)}")
            return False
    
    def test_health_check(self):
        """Test 3: Health Check API"""
        try:
            self.log("Testing health check API...")
            
            response = self.session.get(f"{API_BASE}/health")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    self.log(f"✅ Health check passed: {data}")
                    return True
                else:
                    self.log(f"❌ Health check failed - invalid response: {data}")
                    return False
            else:
                self.log(f"❌ Health check failed - status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Health check test failed: {str(e)}")
            return False
    
    def test_user_registration(self):
        """Test 4: User Registration"""
        try:
            self.log("Testing user registration...")
            
            payload = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "name": "Test User"
            }
            
            response = self.session.post(f"{API_BASE}/auth/register", json=payload)
            
            if response.status_code in [201, 409]:  # 201 = created, 409 = already exists
                if response.status_code == 201:
                    data = response.json()
                    self.log(f"✅ User registration successful: {data.get('message', 'Account created')}")
                else:
                    self.log("✅ User registration - email already exists (expected for repeated tests)")
                return True
            else:
                self.log(f"❌ User registration failed - status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ User registration test failed: {str(e)}")
            return False
    
    def test_user_login(self):
        """Test 5: User Login"""
        try:
            self.log("Testing user login...")
            
            payload = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data:
                    self.auth_token = data['token']
                    self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                    self.log(f"✅ User login successful - token received")
                    return True
                else:
                    self.log(f"❌ User login failed - no token in response: {data}")
                    return False
            else:
                self.log(f"❌ User login failed - status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ User login test failed: {str(e)}")
            return False
    
    def test_file_size_limit(self):
        """Test 6: File Size Limit (50MB)"""
        try:
            self.log("Testing file size limit...")
            
            if not self.auth_token:
                self.log("❌ File size limit test skipped - no auth token")
                return False
            
            # Create a file larger than 50MB
            large_file_size = 51 * 1024 * 1024  # 51MB
            large_file_data = b'0' * large_file_size
            
            files = {'file': ('large_test.pdf', BytesIO(large_file_data), 'application/pdf')}
            
            response = self.session.post(f"{API_BASE}/upload", files=files)
            
            if response.status_code == 400:
                data = response.json()
                if 'too large' in data.get('error', '').lower() or '50mb' in data.get('error', '').lower():
                    self.log("✅ File size limit working - 50MB limit enforced")
                    return True
                else:
                    self.log(f"❌ File size limit failed - unexpected error: {data}")
                    return False
            else:
                self.log(f"❌ File size limit test failed - expected 400, got {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ File size limit test failed: {str(e)}")
            return False
    
    def create_test_pdf(self):
        """Create a simple test PDF for upload testing"""
        try:
            # Create a simple PDF-like file (just for testing upload, not actual PDF processing)
            pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
            return pdf_content
        except Exception as e:
            self.log(f"Error creating test PDF: {str(e)}")
            return None
    
    def test_file_upload(self):
        """Test 7: File Upload"""
        try:
            self.log("Testing file upload...")
            
            if not self.auth_token:
                self.log("❌ File upload test skipped - no auth token")
                return False
            
            # Create test PDF
            pdf_content = self.create_test_pdf()
            if not pdf_content:
                self.log("❌ File upload test failed - could not create test PDF")
                return False
            
            files = {'file': ('test_document.pdf', BytesIO(pdf_content), 'application/pdf')}
            
            response = self.session.post(f"{API_BASE}/upload", files=files)
            
            if response.status_code == 201:
                data = response.json()
                if 'upload' in data and 'id' in data['upload']:
                    self.upload_id = data['upload']['id']
                    self.log(f"✅ File upload successful - upload ID: {self.upload_id}")
                    return True
                else:
                    self.log(f"❌ File upload failed - invalid response format: {data}")
                    return False
            else:
                self.log(f"❌ File upload failed - status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ File upload test failed: {str(e)}")
            return False
    
    def test_ai_processing(self):
        """Test 8: AI Processing"""
        try:
            self.log("Testing AI processing...")
            
            if not self.auth_token or not self.upload_id:
                self.log("❌ AI processing test skipped - no auth token or upload ID")
                return False
            
            payload = {
                "upload_id": self.upload_id
            }
            
            response = self.session.post(f"{API_BASE}/process", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data and 'id' in data['result']:
                    self.result_id = data['result']['id']
                    self.log(f"✅ AI processing successful - result ID: {self.result_id}")
                    self.log(f"   Document type: {data['result'].get('document_type', 'unknown')}")
                    self.log(f"   Columns: {len(data['result'].get('columns', []))}")
                    self.log(f"   Rows: {len(data['result'].get('rows', []))}")
                    return True
                else:
                    self.log(f"❌ AI processing failed - invalid response format: {data}")
                    return False
            else:
                self.log(f"❌ AI processing failed - status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ AI processing test failed: {str(e)}")
            return False
    
    def test_excel_export(self):
        """Test 9: Excel Export (Pre-generated xlsx serving)"""
        try:
            self.log("Testing Excel export...")
            
            if not self.auth_token or not self.result_id:
                self.log("❌ Excel export test skipped - no auth token or result ID")
                return False
            
            response = self.session.get(f"{API_BASE}/export/excel/{self.result_id}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'spreadsheetml' in content_type or 'excel' in content_type:
                    file_size = len(response.content)
                    self.log(f"✅ Excel export successful - file size: {file_size} bytes")
                    self.log(f"   Content-Type: {content_type}")
                    return True
                else:
                    self.log(f"❌ Excel export failed - wrong content type: {content_type}")
                    return False
            else:
                self.log(f"❌ Excel export failed - status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Excel export test failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        self.log("Starting DocXL AI Backend Testing...")
        self.log("=" * 60)
        
        tests = [
            ("Python Imports", self.test_python_imports),
            ("Python Script Execution", self.test_python_script_execution),
            ("Health Check API", self.test_health_check),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("File Size Limit (50MB)", self.test_file_size_limit),
            ("File Upload", self.test_file_upload),
            ("AI Processing", self.test_ai_processing),
            ("Excel Export", self.test_excel_export),
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n--- {test_name} ---")
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    passed += 1
            except Exception as e:
                self.log(f"❌ {test_name} failed with exception: {str(e)}")
                results[test_name] = False
        
        self.log("\n" + "=" * 60)
        self.log("BACKEND TESTING SUMMARY")
        self.log("=" * 60)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status} - {test_name}")
        
        self.log(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 ALL BACKEND TESTS PASSED!")
            return True
        else:
            self.log(f"⚠️  {total - passed} tests failed")
            return False

def main():
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()