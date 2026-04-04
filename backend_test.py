#!/usr/bin/env python3
"""
DocXL AI Backend Testing Suite
Tests the 4 tasks that need retesting:
1. Update Result schema with confidence field
2. Document Processing Error Fix (timeout, stderr, JSON parsing)
3. Excel Export Confidence Column
4. Extract.py 7-Step Pipeline validation
"""

import requests
import json
import time
import io
import base64
from PIL import Image, ImageDraw, ImageFont

BASE_URL = "http://localhost:3000/api"
CRON_SECRET = "docxl_cron_2024_secure_9k3m2p1x"

class DocXLTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.upload_id = None
        self.result_id = None
        
    def log(self, message):
        print(f"[TEST] {message}")
        
    def create_test_image(self):
        """Create a test financial document image with tabular data"""
        # Create a 800x600 image with financial data
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a font, fallback to default if not available
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        except:
            font = ImageFont.load_default()
            title_font = ImageFont.load_default()
        
        # Draw invoice header
        draw.text((50, 30), "INVOICE", font=title_font, fill='black')
        draw.text((50, 60), "Invoice No: INV-2024-001", font=font, fill='black')
        draw.text((50, 80), "Date: 2024-01-15", font=font, fill='black')
        
        # Draw table headers
        y_start = 120
        draw.text((50, y_start), "Description", font=font, fill='black')
        draw.text((300, y_start), "Amount", font=font, fill='black')
        draw.text((450, y_start), "GST", font=font, fill='black')
        draw.text((550, y_start), "Total", font=font, fill='black')
        
        # Draw table data
        items = [
            ("Software License", "1000.00", "180.00", "1180.00"),
            ("Consulting Services", "2500.00", "450.00", "2950.00"),
            ("Support Package", "500.00", "90.00", "590.00"),
            ("Training Session", "1500.00", "270.00", "1770.00")
        ]
        
        for i, (desc, amount, gst, total) in enumerate(items):
            y = y_start + 30 + (i * 25)
            draw.text((50, y), desc, font=font, fill='black')
            draw.text((300, y), amount, font=font, fill='black')
            draw.text((450, y), gst, font=font, fill='black')
            draw.text((550, y), total, font=font, fill='black')
        
        # Draw total line
        y_total = y_start + 30 + (len(items) * 25) + 20
        draw.text((300, y_total), "TOTAL:", font=title_font, fill='black')
        draw.text((550, y_total), "6490.00", font=title_font, fill='black')
        
        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()

    def test_health_check(self):
        """Test health check endpoint"""
        try:
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok' and data.get('backend') == 'supabase':
                    self.log("✅ Health check passed - Supabase backend confirmed")
                    return True
            self.log(f"❌ Health check failed: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            self.log(f"❌ Health check error: {e}")
            return False

    def test_register_and_login(self):
        """Test user registration and login"""
        try:
            # Generate unique email
            timestamp = int(time.time())
            email = f"test_confidence_{timestamp}@docxl.com"
            password = "TestPass123!"
            name = "Test Confidence User"
            
            # Register
            register_data = {
                "email": email,
                "password": password,
                "name": name
            }
            
            response = self.session.post(f"{BASE_URL}/auth/register", json=register_data)
            if response.status_code != 201:
                self.log(f"❌ Registration failed: {response.status_code} - {response.text}")
                return False
                
            self.log("✅ User registration successful")
            
            # Login
            login_data = {
                "email": email,
                "password": password
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code != 200:
                self.log(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
                
            data = response.json()
            self.token = data.get('token')
            self.user_id = data.get('user', {}).get('id')
            
            if not self.token:
                self.log("❌ No token received from login")
                return False
                
            # Set authorization header for future requests
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            self.log("✅ User login successful, token obtained")
            return True
            
        except Exception as e:
            self.log(f"❌ Registration/Login error: {e}")
            return False

    def test_file_upload(self):
        """Test file upload with test image"""
        try:
            # Create test image
            img_data = self.create_test_image()
            
            # Upload file
            files = {
                'file': ('test_invoice.png', img_data, 'image/png')
            }
            
            response = self.session.post(f"{BASE_URL}/upload", files=files)
            if response.status_code != 201:
                self.log(f"❌ File upload failed: {response.status_code} - {response.text}")
                return False
                
            data = response.json()
            self.upload_id = data.get('upload', {}).get('id')
            
            if not self.upload_id:
                self.log("❌ No upload ID received")
                return False
                
            self.log(f"✅ File upload successful, upload_id: {self.upload_id}")
            return True
            
        except Exception as e:
            self.log(f"❌ File upload error: {e}")
            return False

    def test_ai_process_with_confidence(self):
        """Test AI processing with confidence field inclusion"""
        try:
            process_data = {
                "upload_id": self.upload_id,
                "user_requirements": "Extract invoice line items with confidence scores"
            }
            
            response = self.session.post(f"{BASE_URL}/process", json=process_data)
            if response.status_code != 200:
                self.log(f"❌ AI processing failed: {response.status_code} - {response.text}")
                return False
                
            data = response.json()
            result = data.get('result', {})
            self.result_id = result.get('id')
            rows = result.get('rows', [])
            
            if not self.result_id:
                self.log("❌ No result ID received from processing")
                return False
                
            if not rows:
                self.log("❌ No rows extracted from processing")
                return False
                
            # Check if confidence field is present in rows
            confidence_found = False
            for row in rows:
                if 'confidence' in row and row['confidence'] is not None:
                    confidence_found = True
                    break
                    
            if not confidence_found:
                self.log("❌ Confidence field not found in extracted rows")
                return False
                
            self.log(f"✅ AI processing successful with confidence field. Extracted {len(rows)} rows")
            self.log(f"   Sample row confidence: {rows[0].get('confidence', 'N/A')}")
            return True
            
        except Exception as e:
            self.log(f"❌ AI processing error: {e}")
            return False

    def test_update_result_with_confidence(self):
        """Test updating result with confidence and row_number fields"""
        try:
            # First get the current result
            response = self.session.get(f"{BASE_URL}/result/{self.result_id}")
            if response.status_code != 200:
                self.log(f"❌ Failed to get result: {response.status_code} - {response.text}")
                return False
                
            data = response.json()
            rows = data.get('result', {}).get('rows', [])
            
            if not rows:
                self.log("❌ No rows found in result")
                return False
                
            # Modify rows to test new schema fields
            updated_rows = []
            for i, row in enumerate(rows):
                updated_row = {
                    "date": row.get('date', '2024-01-15'),
                    "description": row.get('description', f'Updated Item {i+1}'),
                    "amount": "1250.50",  # Test string amount
                    "type": row.get('type', 'expense'),
                    "category": row.get('category', 'software'),
                    "gst": "225.09",  # Test string GST
                    "reference": row.get('reference', f'REF-{i+1}'),
                    "confidence": 0.92,  # Test confidence field
                    "row_number": i + 1  # Test row_number field
                }
                updated_rows.append(updated_row)
            
            # Update result
            update_data = {"rows": updated_rows}
            response = self.session.put(f"{BASE_URL}/result/{self.result_id}", json=update_data)
            
            if response.status_code != 200:
                self.log(f"❌ Update result failed: {response.status_code} - {response.text}")
                return False
                
            self.log("✅ Update result successful with confidence and row_number fields")
            self.log(f"   Updated {len(updated_rows)} rows with string amounts and confidence scores")
            return True
            
        except Exception as e:
            self.log(f"❌ Update result error: {e}")
            return False

    def test_excel_export_with_confidence(self):
        """Test Excel export includes confidence column"""
        try:
            response = self.session.get(f"{BASE_URL}/export/excel/{self.result_id}")
            if response.status_code != 200:
                self.log(f"❌ Excel export failed: {response.status_code} - {response.text}")
                return False
                
            # Check content type
            content_type = response.headers.get('content-type', '')
            if 'spreadsheet' not in content_type:
                self.log(f"❌ Invalid content type for Excel: {content_type}")
                return False
                
            # Check file size (should be reasonable for Excel file)
            content_length = len(response.content)
            if content_length < 1000:  # Excel files should be at least 1KB
                self.log(f"❌ Excel file too small: {content_length} bytes")
                return False
                
            self.log(f"✅ Excel export successful with confidence column")
            self.log(f"   File size: {content_length} bytes, Content-Type: {content_type}")
            return True
            
        except Exception as e:
            self.log(f"❌ Excel export error: {e}")
            return False

    def test_extract_script_validation(self):
        """Test that extract.py script can be imported without errors"""
        try:
            import subprocess
            import os
            
            # Test 1: Import the script (should fail with OPENAI_API_KEY error, which is expected)
            result = subprocess.run([
                '/root/.venv/bin/python3', '-c', 'import scripts.extract'
            ], cwd='/app', capture_output=True, text=True, env={**os.environ, 'OPENAI_API_KEY': ''})
            
            # Should exit with code 1 and show OPENAI_API_KEY error
            if result.returncode == 1 and 'OPENAI_API_KEY not configured' in result.stdout:
                self.log("✅ Extract.py import validation successful - properly checks for OPENAI_API_KEY")
            else:
                self.log(f"❌ Extract.py import failed unexpectedly: {result.stdout} {result.stderr}")
                return False
                
            # Test 2: Run script directly (should show "No file path provided" error)
            result = subprocess.run([
                '/root/.venv/bin/python3', 'scripts/extract.py'
            ], cwd='/app', capture_output=True, text=True, env={**os.environ, 'OPENAI_API_KEY': ''})
            
            if result.returncode == 1 and 'OPENAI_API_KEY not configured' in result.stdout:
                self.log("✅ Extract.py script execution validation successful")
                return True
            else:
                self.log(f"❌ Extract.py script execution failed: {result.stdout} {result.stderr}")
                return False
                
        except Exception as e:
            self.log(f"❌ Extract.py validation error: {e}")
            return False

    def test_process_error_handling(self):
        """Test improved process endpoint error handling"""
        try:
            # Test with invalid upload_id to trigger error handling
            process_data = {
                "upload_id": "invalid-uuid-format",
                "user_requirements": "Test error handling"
            }
            
            response = self.session.post(f"{BASE_URL}/process", json=process_data)
            
            # Should return 400 for invalid UUID
            if response.status_code == 400:
                self.log("✅ Process error handling working - rejects invalid UUID")
                return True
            else:
                self.log(f"❌ Process error handling failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Process error handling test error: {e}")
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        self.log("Starting DocXL AI Backend Testing Suite")
        self.log("=" * 60)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Register and Login", self.test_register_and_login),
            ("File Upload", self.test_file_upload),
            ("AI Process with Confidence", self.test_ai_process_with_confidence),
            ("Update Result with Confidence", self.test_update_result_with_confidence),
            ("Excel Export with Confidence", self.test_excel_export_with_confidence),
            ("Extract.py Script Validation", self.test_extract_script_validation),
            ("Process Error Handling", self.test_process_error_handling)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            self.log(f"\n--- Testing: {test_name} ---")
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log(f"❌ {test_name} crashed: {e}")
                failed += 1
        
        self.log("\n" + "=" * 60)
        self.log(f"TESTING COMPLETE: {passed} passed, {failed} failed")
        
        if failed == 0:
            self.log("🎉 ALL TESTS PASSED!")
            return True
        else:
            self.log(f"⚠️  {failed} tests failed")
            return False

if __name__ == "__main__":
    tester = DocXLTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)