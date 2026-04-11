#!/usr/bin/env python3
"""
Simple test to verify fallback credit deduction is working
"""

import requests
import json
import uuid

# Configuration
BASE_URL = "https://column-header-fix.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

def test_fallback_credit_deduction():
    """Test that credits are deducted even when AI processing fails"""
    
    # Create unique test user
    test_email = f"test_{uuid.uuid4().hex[:8]}@docxl.com"
    test_password = "testpass123"
    
    print("🧪 Testing Fallback Credit Deduction Mechanism")
    print("=" * 60)
    
    # 1. Register user
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "email": test_email,
        "password": test_password,
        "name": "Test User"
    }, headers=HEADERS)
    
    if response.status_code != 201:
        print(f"❌ Registration failed: {response.text}")
        return False
    
    print(f"✅ User registered: {test_email}")
    
    # 2. Login
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": test_email,
        "password": test_password
    }, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return False
    
    data = response.json()
    access_token = data['token']
    initial_credits = data['user']['credits_remaining']
    print(f"✅ Login successful - Initial credits: {initial_credits}")
    
    # 3. Upload a simple file
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    
    # Create a simple test image
    from io import BytesIO
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='white')
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    files = {'file': ('test.png', img_buffer.getvalue(), 'image/png')}
    response = requests.post(f"{BASE_URL}/upload", files=files, headers=auth_headers)
    
    if response.status_code != 201:
        print(f"❌ Upload failed: {response.text}")
        return False
    
    upload_id = response.json()['upload']['id']
    print(f"✅ File uploaded - Upload ID: {upload_id}")
    
    # 4. Try to process (this will likely fail due to budget, but credits should still be deducted)
    response = requests.post(f"{BASE_URL}/process", json={
        "upload_id": upload_id,
        "user_requirements": "Test processing"
    }, headers={**auth_headers, "Content-Type": "application/json"})
    
    print(f"🔄 Process response: Status {response.status_code}")
    if response.status_code == 500:
        print("⚠️ AI processing failed (expected due to budget limit)")
    elif response.status_code == 200:
        print("✅ AI processing succeeded")
    else:
        print(f"❓ Unexpected status: {response.text}")
    
    # 5. Check credits after processing attempt
    response = requests.get(f"{BASE_URL}/auth/me", headers=auth_headers)
    
    if response.status_code != 200:
        print(f"❌ Get user info failed: {response.text}")
        return False
    
    final_credits = response.json()['user']['credits_remaining']
    print(f"✅ Final credits: {final_credits}")
    
    # 6. Verify credit deduction
    if final_credits == initial_credits - 1:
        print("🎉 SUCCESS: Fallback credit deduction is working correctly!")
        print(f"   Credits deducted: {initial_credits} → {final_credits}")
        return True
    else:
        print(f"❌ FAILURE: Credits not properly deducted")
        print(f"   Expected: {initial_credits - 1}, Got: {final_credits}")
        return False

if __name__ == "__main__":
    success = test_fallback_credit_deduction()
    exit(0 if success else 1)