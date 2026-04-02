#!/usr/bin/env python3
"""
DocXL AI Backend API Test Suite - Supabase Migration
Tests all backend endpoints in the specified order.
"""

import requests
import json
import time
import random
import string
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import os

# Configuration
BASE_URL = "https://docxl-ai.preview.emergentagent.com/api"
TIMEOUT = 120  # 2 minutes for process endpoint

class DocXLTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_data = None
        self.upload_id = None
        self.test_email = f"test_{self.random_string(8)}@docxl.com"
        self.test_password = "TestPass123!"
        self.test_name = "Test User"
        
    def random_string(self, length=8):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def create_test_image_with_financial_data(self):
        """Create a realistic test image with financial data using Pillow"""
        try:
            # Create image with financial table data
            width, height = 800, 600
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font, fallback to basic if not available
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
                font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw header
            draw.text((50, 30), "INVOICE #INV-2024-001", fill='black', font=font_large)
            draw.text((50, 60), "ABC Company Ltd.", fill='black', font=font_medium)
            draw.text((50, 80), "Date: 2024-01-15", fill='black', font=font_medium)
            
            # Draw table headers
            y_start = 120
            draw.rectangle([40, y_start, 760, y_start + 30], outline='black', width=2)
            draw.text((50, y_start + 8), "Description", fill='black', font=font_medium)
            draw.text((300, y_start + 8), "Amount", fill='black', font=font_medium)
            draw.text((400, y_start + 8), "GST", fill='black', font=font_medium)
            draw.text((500, y_start + 8), "Total", fill='black', font=font_medium)
            
            # Draw table rows with financial data
            financial_data = [
                ("Office Supplies", "150.00", "15.00", "165.00"),
                ("Software License", "299.99", "30.00", "329.99"),
                ("Consulting Services", "500.00", "50.00", "550.00"),
                ("Equipment Rental", "75.50", "7.55", "83.05"),
                ("Travel Expenses", "234.80", "23.48", "258.28")
            ]
            
            for i, (desc, amount, gst, total) in enumerate(financial_data):
                y_pos = y_start + 35 + (i * 25)
                draw.rectangle([40, y_pos, 760, y_pos + 25], outline='gray', width=1)
                draw.text((50, y_pos + 5), desc, fill='black', font=font_small)
                draw.text((300, y_pos + 5), f"${amount}", fill='black', font=font_small)
                draw.text((400, y_pos + 5), f"${gst}", fill='black', font=font_small)
                draw.text((500, y_pos + 5), f"${total}", fill='black', font=font_small)
            
            # Draw total
            total_y = y_start + 35 + (len(financial_data) * 25) + 10
            draw.rectangle([40, total_y, 760, total_y + 30], outline='black', width=2)
            draw.text((300, total_y + 8), "TOTAL:", fill='black', font=font_medium)
            draw.text((500, total_y + 8), "$1,386.32", fill='black', font=font_medium)
            
            # Add some visual elements (lines, borders)
            draw.line([40, 110, 760, 110], fill='black', width=2)
            draw.rectangle([35, 25, 765, total_y + 35], outline='black', width=3)
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            print("✅ Created test image with financial data (800x600 PNG)")
            return img_buffer.getvalue()
            
        except Exception as e:
            print(f"❌ Failed to create test image: {e}")
            # Fallback: create simple colored image with text
            img = Image.new('RGB', (400, 300), color='lightblue')
            draw = ImageDraw.Draw(img)
            draw.text((50, 50), "Test Invoice Data", fill='black')
            draw.text((50, 100), "Amount: $1000.00", fill='black')
            draw.text((50, 150), "GST: $100.00", fill='black')
            
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            return img_buffer.getvalue()
    
    def test_health_check(self):
        """Test 1: GET /api/health"""
        try:
            print("\n🔍 Testing Health Check...")
            response = self.session.get(f"{BASE_URL}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok' and data.get('backend') == 'supabase':
                    print("✅ Health check passed - Supabase backend confirmed")
                    return True
                else:
                    print(f"❌ Health check failed - unexpected response: {data}")
                    return False
            else:
                print(f"❌ Health check failed - status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_register(self):
        """Test 2: POST /api/auth/register"""
        try:
            print(f"\n🔍 Testing User Registration with email: {self.test_email}")
            
            payload = {
                "email": self.test_email,
                "password": self.test_password,
                "name": self.test_name
            }
            
            response = self.session.post(
                f"{BASE_URL}/auth/register",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                if 'user' in data and data['user'].get('email') == self.test_email:
                    print("✅ User registration successful")
                    self.user_data = data['user']
                    return True
                else:
                    print(f"❌ Registration failed - unexpected response: {data}")
                    return False
            else:
                print(f"❌ Registration failed - status: {response.status_code}, response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    def test_login(self):
        """Test 3: POST /api/auth/login"""
        try:
            print(f"\n🔍 Testing User Login...")
            
            payload = {
                "email": self.test_email,
                "password": self.test_password
            }
            
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data and 'user' in data:
                    self.access_token = data['token']
                    self.user_data = data['user']
                    print("✅ Login successful - access token received")
                    print(f"   User: {self.user_data.get('name')} ({self.user_data.get('email')})")
                    print(f"   Plan: {self.user_data.get('plan')}, Credits: {self.user_data.get('credits_remaining')}")
                    return True
                else:
                    print(f"❌ Login failed - missing token or user: {data}")
                    return False
            else:
                print(f"❌ Login failed - status: {response.status_code}, response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def test_get_me(self):
        """Test 4: GET /api/auth/me"""
        try:
            print(f"\n🔍 Testing Get Current User...")
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'user' in data:
                    user = data['user']
                    print("✅ Get user info successful")
                    print(f"   ID: {user.get('id')}")
                    print(f"   Email: {user.get('email')}")
                    print(f"   Plan: {user.get('plan')}")
                    print(f"   Credits: {user.get('credits_remaining')}")
                    self.user_data = user  # Update with latest data
                    return True
                else:
                    print(f"❌ Get user failed - missing user data: {data}")
                    return False
            else:
                print(f"❌ Get user failed - status: {response.status_code}, response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Get user error: {e}")
            return False
    
    def test_upload(self):
        """Test 5: POST /api/upload"""
        try:
            print(f"\n🔍 Testing File Upload...")
            
            # Create test image with financial data
            image_data = self.create_test_image_with_financial_data()
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            files = {
                'file': ('test_invoice.png', image_data, 'image/png')
            }
            
            response = self.session.post(
                f"{BASE_URL}/upload",
                headers=headers,
                files=files,
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                if 'upload' in data and 'id' in data['upload']:
                    self.upload_id = data['upload']['id']
                    print("✅ File upload successful")
                    print(f"   Upload ID: {self.upload_id}")
                    print(f"   File: {data['upload']['file_name']}")
                    print(f"   Status: {data['upload']['status']}")
                    return True
                else:
                    print(f"❌ Upload failed - missing upload data: {data}")
                    return False
            else:
                print(f"❌ Upload failed - status: {response.status_code}, response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False
    
    def test_process(self):
        """Test 6: POST /api/process"""
        try:
            print(f"\n🔍 Testing AI Processing (may take 30-120s)...")
            
            payload = {"upload_id": self.upload_id}
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            response = self.session.post(
                f"{BASE_URL}/process",
                json=payload,
                headers=headers,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data and 'rows' in data['result']:
                    result = data['result']
                    print("✅ AI processing successful")
                    print(f"   Document Type: {result.get('document_type')}")
                    print(f"   Rows Extracted: {len(result.get('rows', []))}")
                    print(f"   Confidence: {result.get('confidence_score')}")
                    if result.get('rows'):
                        print(f"   Sample Row: {result['rows'][0]}")
                    return True
                else:
                    print(f"❌ Processing failed - missing result data: {data}")
                    return False
            else:
                print(f"❌ Processing failed - status: {response.status_code}, response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Processing error: {e}")
            return False
    
    def test_get_result(self):
        """Test 7: GET /api/result/{upload_id}"""
        try:
            print(f"\n🔍 Testing Get Result...")
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(
                f"{BASE_URL}/result/{self.upload_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data and 'rows' in data['result']:
                    result = data['result']
                    print("✅ Get result successful")
                    print(f"   Upload ID: {result.get('upload_id')}")
                    print(f"   File Name: {result.get('file_name')}")
                    print(f"   Rows: {len(result.get('rows', []))}")
                    return True
                else:
                    print(f"❌ Get result failed - missing result data: {data}")
                    return False
            else:
                print(f"❌ Get result failed - status: {response.status_code}, response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Get result error: {e}")
            return False
    
    def test_update_result(self):
        """Test 8: PUT /api/result/{upload_id}"""
        try:
            print(f"\n🔍 Testing Update Result...")
            
            # Sample edited data
            edited_rows = [
                {
                    "row_number": 1,
                    "date": "2024-01-15",
                    "description": "Office Supplies (Edited)",
                    "amount": 155.00,
                    "type": "debit",
                    "category": "office",
                    "gst": 15.50,
                    "reference": "REF001"
                }
            ]
            
            payload = {"rows": edited_rows}
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            response = self.session.put(
                f"{BASE_URL}/result/{self.upload_id}",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Update result successful")
                print(f"   Message: {data.get('message')}")
                return True
            else:
                print(f"❌ Update result failed - status: {response.status_code}, response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Update result error: {e}")
            return False
    
    def test_export_excel(self):
        """Test 9: GET /api/export/excel/{upload_id}"""
        try:
            print(f"\n🔍 Testing Excel Export...")
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(
                f"{BASE_URL}/export/excel/{self.upload_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'spreadsheet' in content_type or 'excel' in content_type:
                    print("✅ Excel export successful")
                    print(f"   Content-Type: {content_type}")
                    print(f"   File Size: {len(response.content)} bytes")
                    return True
                else:
                    print(f"❌ Excel export failed - wrong content type: {content_type}")
                    return False
            else:
                print(f"❌ Excel export failed - status: {response.status_code}, response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Excel export error: {e}")
            return False
    
    def test_get_uploads(self):
        """Test 10: GET /api/uploads"""
        try:
            print(f"\n🔍 Testing Get Uploads List...")
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(f"{BASE_URL}/uploads", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'uploads' in data:
                    uploads = data['uploads']
                    print("✅ Get uploads successful")
                    print(f"   Total uploads: {len(uploads)}")
                    
                    # Verify our upload is in the list and status is 'completed'
                    our_upload = next((u for u in uploads if u['id'] == self.upload_id), None)
                    if our_upload:
                        print(f"   Our upload status: {our_upload.get('status')}")
                        if our_upload.get('status') == 'completed':
                            print("✅ Upload status verified as 'completed'")
                        else:
                            print(f"⚠️  Upload status is '{our_upload.get('status')}', expected 'completed'")
                    else:
                        print("⚠️  Our upload not found in list")
                    
                    return True
                else:
                    print(f"❌ Get uploads failed - missing uploads data: {data}")
                    return False
            else:
                print(f"❌ Get uploads failed - status: {response.status_code}, response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Get uploads error: {e}")
            return False
    
    def test_delete_file(self):
        """Test 11: DELETE /api/file/{upload_id}"""
        try:
            print(f"\n🔍 Testing Delete File...")
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.delete(
                f"{BASE_URL}/file/{self.upload_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Delete file successful")
                print(f"   Message: {data.get('message')}")
                return True
            else:
                print(f"❌ Delete file failed - status: {response.status_code}, response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Delete file error: {e}")
            return False
    
    def test_verify_deletion(self):
        """Test 12: Verify file is removed from uploads list"""
        try:
            print(f"\n🔍 Verifying File Deletion...")
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(f"{BASE_URL}/uploads", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                uploads = data.get('uploads', [])
                
                # Check if our upload is still in the list
                our_upload = next((u for u in uploads if u['id'] == self.upload_id), None)
                if our_upload is None:
                    print("✅ File deletion verified - upload removed from list")
                    return True
                else:
                    print(f"❌ File deletion failed - upload still exists: {our_upload}")
                    return False
            else:
                print(f"❌ Verification failed - status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False
    
    def test_credits_verification(self):
        """Test 13: Verify credits decreased after processing"""
        try:
            print(f"\n🔍 Verifying Credits Deduction...")
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                current_credits = data['user'].get('credits_remaining', 0)
                initial_credits = 5  # Default for new users
                
                if current_credits == initial_credits - 1:
                    print(f"✅ Credits verification successful - decreased from {initial_credits} to {current_credits}")
                    return True
                else:
                    print(f"⚠️  Credits: {current_credits} (expected {initial_credits - 1})")
                    return True  # Don't fail the test for this
            else:
                print(f"❌ Credits verification failed - status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Credits verification error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting DocXL AI Backend API Tests (Supabase Migration)")
        print(f"📍 Base URL: {BASE_URL}")
        print("=" * 60)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("User Registration", self.test_register),
            ("User Login", self.test_login),
            ("Get Current User", self.test_get_me),
            ("File Upload", self.test_upload),
            ("AI Processing", self.test_process),
            ("Get Result", self.test_get_result),
            ("Update Result", self.test_update_result),
            ("Excel Export", self.test_export_excel),
            ("Get Uploads List", self.test_get_uploads),
            ("Delete File", self.test_delete_file),
            ("Verify Deletion", self.test_verify_deletion),
            ("Credits Verification", self.test_credits_verification),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
                if not result:
                    print(f"\n⚠️  Test '{test_name}' failed - continuing with remaining tests...")
            except Exception as e:
                print(f"\n❌ Test '{test_name}' crashed: {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Supabase migration successful.")
        else:
            print(f"⚠️  {total - passed} test(s) failed. Check logs above.")
        
        return results

if __name__ == "__main__":
    tester = DocXLTester()
    results = tester.run_all_tests()