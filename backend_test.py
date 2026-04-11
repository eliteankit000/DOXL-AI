#!/usr/bin/env python3
"""
DocXL AI Backend Testing Suite - V3 Extraction System
Tests all critical requirements from the review request.
"""

import sys
import os
import json
import requests
import subprocess
import time
import tempfile
import uuid
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:3000"
API_BASE = f"{BASE_URL}/api"

class BackendTester:
    def __init__(self):
        self.test_results = []
        self.auth_token = None
        self.test_user_email = None
        self.test_upload_id = None
        
    def log_test(self, test_name, success, message="", details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
        if details:
            print(f"    Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details
        })
        
    def test_1_python_imports(self):
        """Test 1: Python Import Verification"""
        try:
            # Test the main import
            result = subprocess.run([
                sys.executable, '-c', 
                "from lib.pdf_engine.extractor import extract_and_build, extract_pdf_content, build_excel, get_extraction_summary; print('OK')"
            ], cwd='/app', capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and 'OK' in result.stdout:
                self.log_test("Python Import Verification", True, "All required functions imported successfully")
            else:
                self.log_test("Python Import Verification", False, f"Import failed: {result.stderr}")
                
        except Exception as e:
            self.log_test("Python Import Verification", False, f"Exception: {str(e)}")
    
    def test_2_banned_strings(self):
        """Test 2: Banned String Check (Zero hardcoded strings)"""
        try:
            banned_strings = ["SAGE", "Semester", "Enrollment", "Subject Details", "Father", "Form Details"]
            extractor_path = "/app/lib/pdf_engine/extractor.py"
            
            if not os.path.exists(extractor_path):
                self.log_test("Banned String Check", False, f"Extractor file not found: {extractor_path}")
                return
                
            with open(extractor_path, 'r') as f:
                content = f.read()
                
            found_banned = []
            for banned in banned_strings:
                if banned in content:
                    found_banned.append(banned)
                    
            if found_banned:
                self.log_test("Banned String Check", False, f"Found hardcoded strings: {found_banned}")
            else:
                self.log_test("Banned String Check", True, "No hardcoded strings found - universal extraction confirmed")
                
        except Exception as e:
            self.log_test("Banned String Check", False, f"Exception: {str(e)}")
    
    def test_3_banned_libraries(self):
        """Test 3: Banned Library Check (Only pdfplumber + openpyxl allowed)"""
        try:
            banned_imports = ["import camelot", "import tabula", "import fitz", "from pymupdf"]
            extractor_path = "/app/lib/pdf_engine/extractor.py"
            
            if not os.path.exists(extractor_path):
                self.log_test("Banned Library Check", False, f"Extractor file not found: {extractor_path}")
                return
                
            with open(extractor_path, 'r') as f:
                content = f.read()
                
            found_banned = []
            for banned in banned_imports:
                if banned in content:
                    found_banned.append(banned)
                    
            if found_banned:
                self.log_test("Banned Library Check", False, f"Found banned imports: {found_banned}")
            else:
                self.log_test("Banned Library Check", True, "Only allowed libraries (pdfplumber + openpyxl) found")
                
        except Exception as e:
            self.log_test("Banned Library Check", False, f"Exception: {str(e)}")
    
    def test_4_graceful_error_handling(self):
        """Test 4: Graceful Error Handling"""
        try:
            # Test with invalid file
            result = subprocess.run([
                sys.executable, '/app/scripts/extract.py', '/dev/null'
            ], cwd='/app', capture_output=True, text=True, timeout=30)
            
            # Should output JSON with error, not crash
            try:
                output = json.loads(result.stdout)
                if 'error' in output:
                    self.log_test("Graceful Error Handling", True, "Script outputs JSON error instead of crashing")
                else:
                    self.log_test("Graceful Error Handling", False, "No error field in JSON output")
            except json.JSONDecodeError:
                self.log_test("Graceful Error Handling", False, f"Script output is not valid JSON: {result.stdout[:200]}")
                
        except Exception as e:
            self.log_test("Graceful Error Handling", False, f"Exception: {str(e)}")
    
    def test_5_health_check(self):
        """Test 5: Health Check API"""
        try:
            response = requests.get(f"{API_BASE}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    self.log_test("Health Check API", True, f"Health check passed: {data}")
                else:
                    self.log_test("Health Check API", False, f"Invalid health response: {data}")
            else:
                self.log_test("Health Check API", False, f"Health check failed with status {response.status_code}")
                
        except Exception as e:
            self.log_test("Health Check API", False, f"Exception: {str(e)}")
    
    def test_6_auth_flow(self):
        """Test 6: Auth Flow (Register + Login)"""
        try:
            # Generate unique test user
            timestamp = int(time.time())
            self.test_user_email = f"test_v3_{timestamp}@docxl.com"
            test_password = "testpass123"
            
            # Test Registration
            reg_data = {
                "email": self.test_user_email,
                "password": test_password,
                "name": "Test User V3"
            }
            
            reg_response = requests.post(f"{API_BASE}/auth/register", json=reg_data, timeout=10)
            
            if reg_response.status_code in [200, 201]:
                self.log_test("User Registration", True, f"User registered: {self.test_user_email}")
            else:
                self.log_test("User Registration", False, f"Registration failed: {reg_response.status_code} - {reg_response.text}")
                return
            
            # Test Login
            login_data = {
                "email": self.test_user_email,
                "password": test_password
            }
            
            login_response = requests.post(f"{API_BASE}/auth/login", json=login_data, timeout=10)
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                self.auth_token = login_data.get('token')
                if self.auth_token:
                    self.log_test("User Login", True, f"Login successful, token received")
                else:
                    self.log_test("User Login", False, "No token in login response")
            else:
                self.log_test("User Login", False, f"Login failed: {login_response.status_code} - {login_response.text}")
                
        except Exception as e:
            self.log_test("Auth Flow", False, f"Exception: {str(e)}")
    
    def test_7_upload_process_flow(self):
        """Test 7: Upload + Process Flow"""
        if not self.auth_token:
            self.log_test("Upload + Process Flow", False, "No auth token available")
            return
            
        try:
            # Create a simple test PDF content
            test_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n174\n%%EOF"
            
            # Upload file
            files = {'file': ('test_v3.pdf', test_content, 'application/pdf')}
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            
            upload_response = requests.post(f"{API_BASE}/upload", files=files, headers=headers, timeout=30)
            
            if upload_response.status_code in [200, 201]:
                upload_data = upload_response.json()
                self.test_upload_id = upload_data.get('upload', {}).get('id')
                if self.test_upload_id:
                    self.log_test("File Upload", True, f"File uploaded successfully: {self.test_upload_id}")
                else:
                    self.log_test("File Upload", False, "No upload ID in response")
                    return
            else:
                self.log_test("File Upload", False, f"Upload failed: {upload_response.status_code} - {upload_response.text}")
                return
            
            # Process file
            process_data = {"upload_id": self.test_upload_id}
            process_response = requests.post(f"{API_BASE}/process", json=process_data, headers=headers, timeout=120)
            
            if process_response.status_code == 200:
                process_result = process_response.json()
                result = process_result.get('result', {})
                if 'columns' in result and 'rows' in result:
                    self.log_test("AI Processing", True, f"Processing successful - Columns: {len(result.get('columns', []))}, Rows: {len(result.get('rows', []))}")
                else:
                    self.log_test("AI Processing", False, f"Invalid process result format: {process_result}")
            else:
                self.log_test("AI Processing", False, f"Processing failed: {process_response.status_code} - {process_response.text}")
                
        except Exception as e:
            self.log_test("Upload + Process Flow", False, f"Exception: {str(e)}")
    
    def test_8_excel_export(self):
        """Test 8: Excel Export (Pre-generated xlsx)"""
        if not self.auth_token or not self.test_upload_id:
            self.log_test("Excel Export", False, "No auth token or upload ID available")
            return
            
        try:
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            export_response = requests.get(f"{API_BASE}/export/excel/{self.test_upload_id}", headers=headers, timeout=30)
            
            if export_response.status_code == 200:
                content_type = export_response.headers.get('content-type', '')
                content_length = len(export_response.content)
                
                if 'spreadsheetml' in content_type and content_length > 0:
                    self.log_test("Excel Export", True, f"Excel export successful - Size: {content_length} bytes, Type: {content_type}")
                else:
                    self.log_test("Excel Export", False, f"Invalid Excel response - Type: {content_type}, Size: {content_length}")
            else:
                self.log_test("Excel Export", False, f"Export failed: {export_response.status_code} - {export_response.text}")
                
        except Exception as e:
            self.log_test("Excel Export", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting DocXL AI V3 Backend Testing Suite")
        print("=" * 60)
        
        # Core V3 Requirements Tests
        self.test_1_python_imports()
        self.test_2_banned_strings()
        self.test_3_banned_libraries()
        self.test_4_graceful_error_handling()
        
        # API Tests
        self.test_5_health_check()
        self.test_6_auth_flow()
        self.test_7_upload_process_flow()
        self.test_8_excel_export()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            
        print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - V3 Extraction System is fully operational!")
        else:
            print("⚠️  Some tests failed - Review issues above")
            
        return passed == total

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)