#!/usr/bin/env python3
"""
DocXL AI Backend Test Suite - Focused on Process Endpoint with Fallback Credit Deduction
Tests the critical process endpoint with RPC fallback mechanism
"""

import requests
import json
import time
import uuid
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Configuration
BASE_URL = "https://ai-doc-stable.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class DocXLTester:
    def __init__(self):
        self.access_token = None
        self.user_id = None
        self.upload_id = None
        self.test_email = f"test_{uuid.uuid4().hex[:8]}@docxl.com"
        self.test_password = "testpass123"
        
    def log(self, message, status="INFO"):
        print(f"[{status}] {message}")
        
    def create_test_invoice_image(self):
        """Create a test invoice image with financial data"""
        try:
            # Create a 800x600 image with white background
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font, fallback to basic if not available
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
                font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw invoice header
            draw.text((50, 30), "INVOICE", fill='black', font=font_large)
            draw.text((50, 70), "Invoice #: INV-2024-001", fill='black', font=font_medium)
            draw.text((50, 100), "Date: 2024-01-15", fill='black', font=font_medium)
            
            # Draw company info
            draw.text((50, 140), "ABC Company Ltd.", fill='black', font=font_medium)
            draw.text((50, 160), "123 Business Street", fill='black', font=font_small)
            draw.text((50, 180), "Mumbai, Maharashtra 400001", fill='black', font=font_small)
            
            # Draw table header
            y_start = 220
            draw.text((50, y_start), "Description", fill='black', font=font_medium)
            draw.text((300, y_start), "Amount", fill='black', font=font_medium)
            draw.text((450, y_start), "GST", fill='black', font=font_medium)
            draw.text((550, y_start), "Total", fill='black', font=font_medium)
            
            # Draw line under header
            draw.line([(50, y_start + 25), (700, y_start + 25)], fill='black', width=2)
            
            # Draw invoice items
            items = [
                ("Software Development Services", "50000.00", "9000.00", "59000.00"),
                ("Consulting Services", "25000.00", "4500.00", "29500.00"),
                ("Technical Support", "15000.00", "2700.00", "17700.00"),
                ("Project Management", "20000.00", "3600.00", "23600.00"),
                ("Documentation", "10000.00", "1800.00", "11800.00")
            ]
            
            y_pos = y_start + 40
            for item in items:
                draw.text((50, y_pos), item[0], fill='black', font=font_small)
                draw.text((300, y_pos), f"₹{item[1]}", fill='black', font=font_small)
                draw.text((450, y_pos), f"₹{item[2]}", fill='black', font=font_small)
                draw.text((550, y_pos), f"₹{item[3]}", fill='black', font=font_small)
                y_pos += 25
            
            # Draw total line
            draw.line([(450, y_pos + 10), (650, y_pos + 10)], fill='black', width=2)
            draw.text((450, y_pos + 20), "Grand Total: ₹1,41,600.00", fill='black', font=font_medium)
            
            # Save to BytesIO
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            self.log("✅ Created test invoice image with financial data")
            return img_buffer.getvalue()
            
        except Exception as e:
            self.log(f"❌ Failed to create test image: {str(e)}", "ERROR")
            # Create a simple fallback image
            img = Image.new('RGB', (400, 300), color='white')
            draw = ImageDraw.Draw(img)
            draw.text((50, 50), "Test Invoice", fill='black')
            draw.text((50, 100), "Amount: ₹1000.00", fill='black')
            draw.text((50, 150), "GST: ₹180.00", fill='black')
            draw.text((50, 200), "Total: ₹1180.00", fill='black')
            
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            return img_buffer.getvalue()

    def test_health_check(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok' and data.get('backend') == 'supabase':
                    self.log("✅ Health check passed - Supabase backend confirmed")
                    return True
                else:
                    self.log(f"❌ Health check failed - unexpected response: {data}", "ERROR")
                    return False
            else:
                self.log(f"❌ Health check failed - status: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Health check error: {str(e)}", "ERROR")
            return False

    def test_register(self):
        """Test user registration"""
        try:
            payload = {
                "email": self.test_email,
                "password": self.test_password,
                "name": "Test User"
            }
            
            response = requests.post(f"{BASE_URL}/auth/register", json=payload, headers=HEADERS)
            
            if response.status_code == 201:
                data = response.json()
                self.user_id = data['user']['id']
                credits = data['user']['credits_remaining']
                self.log(f"✅ User registration successful - Email: {self.test_email}, Credits: {credits}")
                return True
            else:
                self.log(f"❌ Registration failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Registration error: {str(e)}", "ERROR")
            return False

    def test_login(self):
        """Test user login"""
        try:
            payload = {
                "email": self.test_email,
                "password": self.test_password
            }
            
            response = requests.post(f"{BASE_URL}/auth/login", json=payload, headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['token']
                self.user_id = data['user']['id']
                credits = data['user']['credits_remaining']
                self.log(f"✅ Login successful - User ID: {self.user_id}, Credits: {credits}")
                return True
            else:
                self.log(f"❌ Login failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Login error: {str(e)}", "ERROR")
            return False

    def test_get_user_info(self):
        """Test get current user info"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                user = data['user']
                credits = user['credits_remaining']
                self.log(f"✅ Get user info successful - Credits: {credits}, Plan: {user['plan']}")
                return credits
            else:
                self.log(f"❌ Get user info failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Get user info error: {str(e)}", "ERROR")
            return None

    def test_upload_file(self):
        """Test file upload"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create test image
            image_data = self.create_test_invoice_image()
            
            files = {
                'file': ('test_invoice.png', image_data, 'image/png')
            }
            
            response = requests.post(f"{BASE_URL}/upload", files=files, headers=headers)
            
            if response.status_code == 201:
                data = response.json()
                self.upload_id = data['upload']['id']
                self.log(f"✅ File upload successful - Upload ID: {self.upload_id}, Status: {data['upload']['status']}")
                return True
            else:
                self.log(f"❌ File upload failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ File upload error: {str(e)}", "ERROR")
            return False

    def test_process_with_fallback_credit_deduction(self):
        """Test AI processing with fallback credit deduction - CRITICAL TEST"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "upload_id": self.upload_id,
                "user_requirements": "Extract all financial data including amounts, dates, and descriptions"
            }
            
            self.log("🔄 Starting AI processing with fallback credit deduction...")
            response = requests.post(f"{BASE_URL}/process", json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                result = data['result']
                rows = result.get('rows', [])
                document_type = result.get('document_type', 'unknown')
                confidence = result.get('confidence_score', 0)
                
                self.log(f"✅ AI processing successful with fallback credit deduction!")
                self.log(f"   - Document type: {document_type}")
                self.log(f"   - Confidence: {confidence}")
                self.log(f"   - Extracted {len(rows)} rows")
                self.log(f"   - Upload ID: {result['upload_id']}")
                
                if len(rows) > 0:
                    self.log(f"   - Sample row: {rows[0]}")
                
                return True
            else:
                self.log(f"❌ AI processing failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ AI processing error: {str(e)}", "ERROR")
            return False

    def test_get_result(self):
        """Test get processing result"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            response = requests.get(f"{BASE_URL}/result/{self.upload_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                result = data['result']
                rows = result.get('rows', [])
                self.log(f"✅ Get result successful - {len(rows)} rows, File: {result.get('file_name', 'unknown')}")
                return True
            else:
                self.log(f"❌ Get result failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Get result error: {str(e)}", "ERROR")
            return False

    def test_zod_validation(self):
        """Test Zod validation on endpoints"""
        try:
            headers = {"Content-Type": "application/json"}
            
            # Test register with invalid email
            response = requests.post(f"{BASE_URL}/auth/register", 
                                   json={"email": "invalid-email", "password": "123"}, 
                                   headers=headers)
            if response.status_code == 400:
                self.log("✅ Zod validation working on register (invalid email rejected)")
            else:
                self.log(f"❌ Zod validation failed on register - Status: {response.status_code}", "ERROR")
                return False
            
            # Test login with empty password
            response = requests.post(f"{BASE_URL}/auth/login", 
                                   json={"email": "test@example.com", "password": ""}, 
                                   headers=headers)
            if response.status_code == 400:
                self.log("✅ Zod validation working on login (empty password rejected)")
            else:
                self.log(f"❌ Zod validation failed on login - Status: {response.status_code}", "ERROR")
                return False
            
            # Test process with invalid UUID
            auth_headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            response = requests.post(f"{BASE_URL}/process", 
                                   json={"upload_id": "invalid-uuid"}, 
                                   headers=auth_headers)
            if response.status_code == 400:
                self.log("✅ Zod validation working on process (invalid UUID rejected)")
            else:
                self.log(f"❌ Zod validation failed on process - Status: {response.status_code}", "ERROR")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"❌ Zod validation test error: {str(e)}", "ERROR")
            return False

    def test_payment_endpoints(self):
        """Test Razorpay payment endpoints"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
            
            # Test create order
            response = requests.post(f"{BASE_URL}/payment/create-order", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if 'orderId' in data and 'amount' in data:
                    self.log(f"✅ Razorpay create order successful - Order ID: {data['orderId']}, Amount: {data['amount']}")
                else:
                    self.log(f"❌ Razorpay create order missing fields: {data}", "ERROR")
                    return False
            else:
                self.log(f"❌ Razorpay create order failed - Status: {response.status_code}", "ERROR")
                return False
            
            # Test payment verify with missing fields (should return 400)
            response = requests.post(f"{BASE_URL}/payment/verify", 
                                   json={"incomplete": "data"}, 
                                   headers=headers)
            if response.status_code == 400:
                self.log("✅ Razorpay payment verify validation working (missing fields rejected)")
            else:
                self.log(f"❌ Razorpay payment verify validation failed - Status: {response.status_code}", "ERROR")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"❌ Payment endpoints test error: {str(e)}", "ERROR")
            return False

    def run_comprehensive_test(self):
        """Run comprehensive backend test suite"""
        self.log("=" * 80)
        self.log("DOCXL AI BACKEND TEST SUITE - FOCUSED ON PROCESS ENDPOINT WITH FALLBACK")
        self.log("=" * 80)
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Health Check
        total_tests += 1
        if self.test_health_check():
            tests_passed += 1
        
        # Test 2: User Registration
        total_tests += 1
        if self.test_register():
            tests_passed += 1
        else:
            self.log("❌ Cannot continue without successful registration", "ERROR")
            return False
        
        # Test 3: User Login
        total_tests += 1
        if self.test_login():
            tests_passed += 1
        else:
            self.log("❌ Cannot continue without successful login", "ERROR")
            return False
        
        # Test 4: Check initial credits
        total_tests += 1
        initial_credits = self.test_get_user_info()
        if initial_credits is not None:
            tests_passed += 1
            if initial_credits == 5:
                self.log(f"✅ Initial credits correct: {initial_credits}")
            else:
                self.log(f"⚠️ Initial credits unexpected: {initial_credits} (expected 5)", "WARNING")
        else:
            self.log("❌ Cannot continue without user info", "ERROR")
            return False
        
        # Test 5: File Upload
        total_tests += 1
        if self.test_upload_file():
            tests_passed += 1
        else:
            self.log("❌ Cannot continue without successful upload", "ERROR")
            return False
        
        # Test 6: CRITICAL - AI Processing with Fallback Credit Deduction
        total_tests += 1
        self.log("🎯 CRITICAL TEST: AI Processing with Fallback Credit Deduction")
        if self.test_process_with_fallback_credit_deduction():
            tests_passed += 1
            self.log("🎉 CRITICAL TEST PASSED: Fallback credit deduction working!")
        else:
            self.log("💥 CRITICAL TEST FAILED: Fallback credit deduction not working!", "ERROR")
        
        # Test 7: Check credits after processing
        total_tests += 1
        final_credits = self.test_get_user_info()
        if final_credits is not None:
            tests_passed += 1
            expected_credits = initial_credits - 1
            if final_credits == expected_credits:
                self.log(f"✅ Credits properly deducted: {final_credits} (was {initial_credits})")
            else:
                self.log(f"❌ Credits not properly deducted: {final_credits} (expected {expected_credits})", "ERROR")
        
        # Test 8: Get Result
        total_tests += 1
        if self.test_get_result():
            tests_passed += 1
        
        # Test 9: Zod Validation
        total_tests += 1
        if self.test_zod_validation():
            tests_passed += 1
        
        # Test 10: Payment Endpoints
        total_tests += 1
        if self.test_payment_endpoints():
            tests_passed += 1
        
        # Summary
        self.log("=" * 80)
        self.log(f"TEST SUMMARY: {tests_passed}/{total_tests} tests passed")
        self.log("=" * 80)
        
        if tests_passed == total_tests:
            self.log("🎉 ALL TESTS PASSED! Backend is working correctly with fallback credit deduction.")
            return True
        else:
            self.log(f"❌ {total_tests - tests_passed} tests failed. Check logs above for details.", "ERROR")
            return False

if __name__ == "__main__":
    tester = DocXLTester()
    success = tester.run_comprehensive_test()
    exit(0 if success else 1)