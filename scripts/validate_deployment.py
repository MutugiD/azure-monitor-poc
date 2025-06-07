#!/usr/bin/env python3
"""
Simple deployment validation script
Tests basic functionality of the API monitoring pipeline
"""

import requests
import json
from datetime import datetime
import uuid

def test_endpoint(url, data):
    """Test a single endpoint"""
    try:
        response = requests.post(
            url,
            json=data,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        return response.status_code, response.text
    except Exception as e:
        return None, str(e)

def main():
    print("🔍 Validating Azure API Monitoring Deployment")
    print("=" * 50)

    # Configuration
    function_base_url = "https://azurepoc-function-app.azurewebsites.net"

    # Test data
    test_event = {
        "eventType": "ValidationTest",
        "sourceSystem": "Salesforce",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "eventId": str(uuid.uuid4()),
        "userId": "test-user",
        "action": "validation"
    }

    # Test endpoints
    endpoints = [
        ("salesforceloghandler", "Salesforce Log Handler"),
        ("mulesoftloghandler", "MuleSoft Log Handler"),
        ("universalloghandler", "Universal Log Handler")
    ]

    results = []

    for endpoint, name in endpoints:
        print(f"\n🧪 Testing {name}...")
        url = f"{function_base_url}/api/{endpoint}"
        status_code, response = test_endpoint(url, test_event)

        if status_code == 200:
            print(f"✅ {name}: SUCCESS (Status: {status_code})")
            results.append(True)
        elif status_code:
            print(f"❌ {name}: FAILED (Status: {status_code})")
            print(f"   Response: {response[:200]}...")
            results.append(False)
        else:
            print(f"❌ {name}: CONNECTION ERROR")
            print(f"   Error: {response}")
            results.append(False)

    # Summary
    print("\n" + "=" * 50)
    print("📊 Validation Summary")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    if passed == total:
        print("🎉 All endpoints are working correctly!")
        print("\n📋 Next Steps:")
        print("1. Run full test suite: python test_complete_pipeline.py")
        print("2. Check Azure Portal for dashboard data")
        print("3. View Log Analytics workspace for events")
    else:
        print("⚠️ Some endpoints failed. Check Azure Function logs.")
        print("\n🔧 Troubleshooting:")
        print("1. Verify Function App is running in Azure Portal")
        print("2. Check Function App logs for errors")
        print("3. Ensure all environment variables are set")

    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)