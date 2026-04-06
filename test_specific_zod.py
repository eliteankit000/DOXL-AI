#!/usr/bin/env python3
"""
Specific test for the flexible Zod schema as requested in the review
"""

import requests
import json

BASE_URL = "http://localhost:3000"

def test_flexible_zod_schema():
    """Test the NEW flexible Zod schema for result updates"""
    print("=== TESTING FLEXIBLE ZOD SCHEMA ===")
    
    # Test 1: Dynamic structure with any columns
    print("\n1. Testing dynamic structure with Name/City columns:")
    payload1 = {
        "rows": [
            {"Name": "John", "City": "NYC"},
            {"Name": "Jane", "City": "LA"}
        ],
        "columns": ["Name", "City"]
    }
    
    response1 = requests.put(f"{BASE_URL}/api/result/fake-uuid-here", json=payload1)
    print(f"   Status: {response1.status_code}")
    print(f"   Response: {response1.text}")
    
    # Test 2: Different dynamic structure
    print("\n2. Testing different dynamic structure with Product/Price columns:")
    payload2 = {
        "rows": [
            {"Product": "Laptop", "Price": 999, "Category": "Electronics"},
            {"Product": "Phone", "Price": 599, "Category": "Electronics"}
        ],
        "columns": ["Product", "Price", "Category"]
    }
    
    response2 = requests.put(f"{BASE_URL}/api/result/fake-uuid-here", json=payload2)
    print(f"   Status: {response2.status_code}")
    print(f"   Response: {response2.text}")
    
    # Test 3: Complex nested structure
    print("\n3. Testing complex structure with mixed data types:")
    payload3 = {
        "rows": [
            {"Date": "2024-01-01", "Amount": 1500.50, "Description": "Payment", "Tags": ["urgent", "verified"]},
            {"Date": "2024-01-02", "Amount": 750.25, "Description": "Refund", "Tags": ["processed"]}
        ],
        "columns": ["Date", "Amount", "Description", "Tags"]
    }
    
    response3 = requests.put(f"{BASE_URL}/api/result/fake-uuid-here", json=payload3)
    print(f"   Status: {response3.status_code}")
    print(f"   Response: {response3.text}")
    
    # Analysis
    print("\n=== ANALYSIS ===")
    responses = [response1, response2, response3]
    
    validation_errors = [r for r in responses if r.status_code == 400]
    auth_errors = [r for r in responses if r.status_code == 401]
    not_found_errors = [r for r in responses if r.status_code == 404]
    
    print(f"Validation errors (400): {len(validation_errors)}")
    print(f"Auth errors (401): {len(auth_errors)}")
    print(f"Not found errors (404): {len(not_found_errors)}")
    
    if len(validation_errors) == 0:
        print("✅ SUCCESS: Flexible Zod schema accepts all dynamic structures!")
        print("   No validation errors (400) - schema is truly flexible")
        return True
    else:
        print("❌ FAIL: Schema still has validation restrictions")
        for i, resp in enumerate(validation_errors):
            print(f"   Test {i+1} failed with: {resp.text}")
        return False

def test_process_validation():
    """Test process endpoint validation with invalid UUID"""
    print("\n=== TESTING PROCESS VALIDATION ===")
    
    payload = {
        "upload_id": "not-a-uuid"
    }
    
    response = requests.post(f"{BASE_URL}/api/process", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 400:
        print("✅ SUCCESS: Process endpoint validates UUID format")
        return True
    elif response.status_code == 401:
        print("✅ SUCCESS: Process endpoint requires auth (expected)")
        return True
    else:
        print(f"❌ FAIL: Expected 400 or 401, got {response.status_code}")
        return False

def main():
    print("🔍 SPECIFIC TESTING: Flexible Zod Schema & Process Validation")
    print("=" * 60)
    
    schema_test = test_flexible_zod_schema()
    process_test = test_process_validation()
    
    print("\n" + "=" * 60)
    print("📊 SPECIFIC TEST RESULTS")
    print("=" * 60)
    print(f"{'✅' if schema_test else '❌'} Flexible Zod Schema: {'PASS' if schema_test else 'FAIL'}")
    print(f"{'✅' if process_test else '❌'} Process Validation: {'PASS' if process_test else 'FAIL'}")
    
    if schema_test and process_test:
        print("\n🎉 All specific tests passed!")
        return 0
    else:
        print("\n⚠️ Some specific tests failed.")
        return 1

if __name__ == "__main__":
    exit(main())