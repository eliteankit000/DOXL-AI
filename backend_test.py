#!/usr/bin/env python3
"""
DocXL AI Backend API Test Suite
Tests all backend endpoints in the correct order with proper authentication.
"""
import requests
import json
import time
import base64
import io
from PIL import Image, ImageDraw, ImageFont
import os
import sys

# API Configuration
API_BASE = "https://docxl-ai.preview.emergentagent.com/api"
TEST_EMAIL = "test.user.docxl@example.com"
TEST_PASSWORD = "SecureTestPass123!"
TEST_NAME = "DocXL Test User"

# Global variables for test state
auth_token = None
test_upload_id = None
test_result_id = None

def create_test_image():
    """Create a test image with financial data table for AI processing."""
    # Create a 800x600 image with white background
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fallback to basic if not available
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        font_data = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font_title = ImageFont.load_default()
        font_header = ImageFont.load_default()
        font_data = ImageFont.load_default()
    
    # Draw title
    draw.text((50, 30), "FINANCIAL STATEMENT - Q4 2024", fill='black', font=font_title)
    
    # Draw table headers
    headers = ["Date", "Description", "Amount", "Type", "Category"]
    header_y = 80
    col_widths = [100, 250, 100, 80, 120]
    col_x = [50, 150, 400, 500, 580]
    
    # Draw header background
    draw.rectangle([45, header_y-5, 750, header_y+25], fill='lightgray', outline='black')
    
    for i, header in enumerate(headers):
        draw.text((col_x[i], header_y), header, fill='black', font=font_header)
    
    # Draw table data
    data_rows = [
        ["2024-12-01", "Office Supplies Purchase", "1250.00", "Debit", "Office"],
        ["2024-12-02", "Client Payment Received", "5000.00", "Credit", "Revenue"],
        ["2024-12-03", "Software License Fee", "299.99", "Debit", "Software"],
        ["2024-12-04", "Marketing Campaign", "750.50", "Debit", "Marketing"],
        ["2024-12-05", "Consulting Revenue", "2500.00", "Credit", "Revenue"],
        ["2024-12-06", "Utility Bills", "180.25", "Debit", "Utilities"],
        ["2024-12-07", "Equipment Purchase", "3200.00", "Debit", "Equipment"],
        ["2024-12-08", "Service Income", "1800.00", "Credit", "Revenue"]
    ]
    
    row_height = 25
    for i, row in enumerate(data_rows):
        y_pos = header_y + 30 + (i * row_height)
        
        # Alternate row background
        if i % 2 == 0:
            draw.rectangle([45, y_pos-2, 750, y_pos+20], fill='#f8f9fa', outline='lightgray')
        
        for j, cell in enumerate(row):
            draw.text((col_x[j], y_pos), cell, fill='black', font=font_data)
    
    # Draw table border
    draw.rectangle([45, header_y-5, 750, header_y + 30 + (len(data_rows) * row_height)], 
                  fill=None, outline='black', width=2)
    
    # Add total row
    total_y = header_y + 30 + (len(data_rows) * row_height) + 10
    draw.rectangle([45, total_y, 750, total_y + 25], fill='lightblue', outline='black')
    draw.text((col_x[0], total_y + 5), "TOTAL", fill='black', font=font_header)
    draw.text((col_x[2], total_y + 5), "14,980.74", fill='black', font=font_header)
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()

def test_health_check():
    """Test GET /api/health endpoint."""
    print("\n=== Testing Health Check API ===")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                print("✅ Health check passed")
                return True
            else:
                print("❌ Health check failed - invalid response")
                return False
        else:
            print(f"❌ Health check failed - status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed - error: {e}")
        return False

def test_user_registration():
    """Test POST /api/auth/register endpoint."""
    print("\n=== Testing User Registration API ===")
    try:
        payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": TEST_NAME
        }
        
        response = requests.post(f"{API_BASE}/auth/register", 
                               json=payload, 
                               timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code in [201, 409]:  # 201 = created, 409 = already exists
            data = response.json()
            if response.status_code == 201:
                global auth_token
                auth_token = data.get('token')
                print("✅ User registration successful")
                return True
            elif response.status_code == 409 and 'already registered' in data.get('error', ''):
                print("✅ User already exists (expected for repeated tests)")
                return True
        
        print(f"❌ User registration failed - status {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ User registration failed - error: {e}")
        return False

def test_user_login():
    """Test POST /api/auth/login endpoint."""
    print("\n=== Testing User Login API ===")
    try:
        payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = requests.post(f"{API_BASE}/auth/login", 
                               json=payload, 
                               timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            user = data.get('user')
            
            if token and user:
                global auth_token
                auth_token = token
                print("✅ User login successful")
                print(f"User ID: {user.get('id')}")
                print(f"Email: {user.get('email')}")
                return True
            else:
                print("❌ Login failed - missing token or user data")
                return False
        else:
            print(f"❌ User login failed - status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ User login failed - error: {e}")
        return False

def test_get_current_user():
    """Test GET /api/auth/me endpoint."""
    print("\n=== Testing Get Current User API ===")
    try:
        if not auth_token:
            print("❌ No auth token available")
            return False
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{API_BASE}/auth/me", 
                              headers=headers, 
                              timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            user = data.get('user')
            
            if user and user.get('email') == TEST_EMAIL:
                print("✅ Get current user successful")
                print(f"Credits remaining: {user.get('credits_remaining')}")
                return True
            else:
                print("❌ Get current user failed - invalid user data")
                return False
        else:
            print(f"❌ Get current user failed - status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get current user failed - error: {e}")
        return False

def test_file_upload():
    """Test POST /api/upload endpoint."""
    print("\n=== Testing File Upload API ===")
    try:
        if not auth_token:
            print("❌ No auth token available")
            return False
        
        # Create test image
        image_data = create_test_image()
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        files = {
            'file': ('test_financial_data.png', image_data, 'image/png')
        }
        
        response = requests.post(f"{API_BASE}/upload", 
                               headers=headers,
                               files=files,
                               timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            data = response.json()
            upload = data.get('upload')
            
            if upload and upload.get('id'):
                global test_upload_id
                test_upload_id = upload.get('id')
                print("✅ File upload successful")
                print(f"Upload ID: {test_upload_id}")
                print(f"File name: {upload.get('file_name')}")
                print(f"Status: {upload.get('status')}")
                return True
            else:
                print("❌ File upload failed - missing upload data")
                return False
        else:
            print(f"❌ File upload failed - status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ File upload failed - error: {e}")
        return False

def test_ai_process():
    """Test POST /api/process endpoint."""
    print("\n=== Testing AI Process API ===")
    try:
        if not auth_token or not test_upload_id:
            print("❌ No auth token or upload ID available")
            return False
        
        payload = {"upload_id": test_upload_id}
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        print("Starting AI processing (may take 30-60 seconds)...")
        response = requests.post(f"{API_BASE}/process", 
                               json=payload,
                               headers=headers,
                               timeout=120)  # 2 minute timeout for AI processing
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('result')
            
            if result and result.get('id'):
                global test_result_id
                test_result_id = result.get('id')
                print("✅ AI processing successful")
                print(f"Result ID: {test_result_id}")
                print(f"Document type: {result.get('document_type')}")
                print(f"Rows extracted: {len(result.get('rows', []))}")
                print(f"Confidence score: {result.get('confidence_score')}")
                return True
            else:
                print("❌ AI processing failed - missing result data")
                return False
        else:
            print(f"❌ AI processing failed - status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ AI processing failed - error: {e}")
        return False

def test_get_result():
    """Test GET /api/result/{id} endpoint."""
    print("\n=== Testing Get Result API ===")
    try:
        if not auth_token or not test_upload_id:
            print("❌ No auth token or upload ID available")
            return False
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{API_BASE}/result/{test_upload_id}", 
                              headers=headers,
                              timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('result')
            
            if result and result.get('rows'):
                print("✅ Get result successful")
                print(f"Upload ID: {result.get('upload_id')}")
                print(f"Document type: {result.get('document_type')}")
                print(f"Number of rows: {len(result.get('rows'))}")
                print(f"File name: {result.get('file_name')}")
                return True
            else:
                print("❌ Get result failed - missing result data")
                return False
        else:
            print(f"❌ Get result failed - status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get result failed - error: {e}")
        return False

def test_export_excel():
    """Test GET /api/export/excel/{id} endpoint."""
    print("\n=== Testing Export Excel API ===")
    try:
        if not auth_token or not test_upload_id:
            print("❌ No auth token or upload ID available")
            return False
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{API_BASE}/export/excel/{test_upload_id}", 
                              headers=headers,
                              timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Content-Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'spreadsheetml' in content_type or 'excel' in content_type:
                print("✅ Excel export successful")
                print(f"Excel file size: {len(response.content)} bytes")
                return True
            else:
                print(f"❌ Excel export failed - wrong content type: {content_type}")
                return False
        else:
            print(f"❌ Excel export failed - status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Excel export failed - error: {e}")
        return False

def test_list_uploads():
    """Test GET /api/uploads endpoint."""
    print("\n=== Testing List Uploads API ===")
    try:
        if not auth_token:
            print("❌ No auth token available")
            return False
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{API_BASE}/uploads", 
                              headers=headers,
                              timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            uploads = data.get('uploads', [])
            
            print("✅ List uploads successful")
            print(f"Number of uploads: {len(uploads)}")
            
            # Check if our test upload is in the list
            test_upload_found = any(u.get('id') == test_upload_id for u in uploads)
            if test_upload_found:
                print(f"✅ Test upload {test_upload_id} found in list")
            else:
                print(f"⚠️ Test upload {test_upload_id} not found in list")
            
            return True
        else:
            print(f"❌ List uploads failed - status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ List uploads failed - error: {e}")
        return False

def test_update_result():
    """Test PUT /api/result/{id} endpoint."""
    print("\n=== Testing Update Result API ===")
    try:
        if not auth_token or not test_upload_id:
            print("❌ No auth token or upload ID available")
            return False
        
        # First get the current result to modify
        headers = {"Authorization": f"Bearer {auth_token}"}
        get_response = requests.get(f"{API_BASE}/result/{test_upload_id}", 
                                  headers=headers,
                                  timeout=10)
        
        if get_response.status_code != 200:
            print("❌ Could not get current result for update test")
            return False
        
        current_result = get_response.json().get('result', {})
        current_rows = current_result.get('rows', [])
        
        if not current_rows:
            print("❌ No rows to update")
            return False
        
        # Modify the first row
        updated_rows = current_rows.copy()
        if len(updated_rows) > 0:
            updated_rows[0]['description'] = 'UPDATED: ' + updated_rows[0].get('description', '')
            updated_rows[0]['amount'] = 9999.99
        
        # Add a new row
        new_row = {
            "id": "test-new-row",
            "row_number": len(updated_rows) + 1,
            "date": "2024-12-31",
            "description": "Test Update - New Row Added",
            "amount": 500.00,
            "type": "credit",
            "category": "Test",
            "gst": 50.00,
            "reference": "TEST-UPDATE"
        }
        updated_rows.append(new_row)
        
        payload = {"rows": updated_rows}
        
        response = requests.put(f"{API_BASE}/result/{test_upload_id}", 
                              json=payload,
                              headers=headers,
                              timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Update result successful")
            print(f"Updated {len(updated_rows)} rows")
            return True
        else:
            print(f"❌ Update result failed - status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Update result failed - error: {e}")
        return False

def test_delete_file():
    """Test DELETE /api/file/{id} endpoint."""
    print("\n=== Testing Delete File API ===")
    try:
        if not auth_token or not test_upload_id:
            print("❌ No auth token or upload ID available")
            return False
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.delete(f"{API_BASE}/file/{test_upload_id}", 
                                 headers=headers,
                                 timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if 'deleted' in data.get('message', '').lower():
                print("✅ Delete file successful")
                return True
            else:
                print("❌ Delete file failed - unexpected response")
                return False
        else:
            print(f"❌ Delete file failed - status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Delete file failed - error: {e}")
        return False

def run_all_tests():
    """Run all backend API tests in sequence."""
    print("🚀 Starting DocXL AI Backend API Test Suite")
    print(f"API Base URL: {API_BASE}")
    print("=" * 60)
    
    test_results = {}
    
    # Test in the specified order
    tests = [
        ("Health Check", test_health_check),
        ("User Registration", test_user_registration),
        ("User Login", test_user_login),
        ("Get Current User", test_get_current_user),
        ("File Upload", test_file_upload),
        ("AI Process", test_ai_process),
        ("Get Result", test_get_result),
        ("Export Excel", test_export_excel),
        ("List Uploads", test_list_uploads),
        ("Update Result", test_update_result),
        ("Delete File", test_delete_file)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results[test_name] = result
            time.sleep(1)  # Brief pause between tests
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            test_results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal Tests: {len(test_results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(test_results)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Backend API is working correctly.")
        return True
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test suite failed with error: {e}")
        sys.exit(1)