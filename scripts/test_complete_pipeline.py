#!/usr/bin/env python3
"""
Comprehensive Pipeline Test Suite
Tests the complete Salesforce + MuleSoft API monitoring pipeline
"""

import sys
import os
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import uuid

# Add the current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from api_simulator import MultiAPIEventSimulator

class PipelineTestSuite:
    def __init__(self, function_base_url: str, workspace_id: str):
        self.function_base_url = function_base_url.rstrip('/')
        self.workspace_id = workspace_id
        self.simulator = MultiAPIEventSimulator(function_base_url)
        self.test_results = []

    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")

    def test_function_endpoints(self) -> bool:
        """Test all Azure Function endpoints"""
        print("\n🧪 Testing Function Endpoints")
        print("-" * 40)

        endpoints = [
            ("salesforceloghandler", self.simulator.generate_sf_login_event()),
            ("mulesoftloghandler", self.simulator.generate_mulesoft_performance_event()),
            ("universalloghandler", self.simulator.generate_sf_api_event())
        ]

        all_passed = True

        for endpoint, test_event in endpoints:
            try:
                url = f"{self.function_base_url}/api/{endpoint}"
                response = requests.post(
                    url,
                    json=test_event,
                    timeout=10,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    self.log_test(f"Endpoint {endpoint}", "PASS", f"Status: {response.status_code}")
                else:
                    self.log_test(f"Endpoint {endpoint}", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                    all_passed = False

            except Exception as e:
                self.log_test(f"Endpoint {endpoint}", "FAIL", f"Exception: {str(e)}")
                all_passed = False

        return all_passed

    def test_event_generation(self) -> bool:
        """Test event generation for all types"""
        print("\n🧪 Testing Event Generation")
        print("-" * 40)

        generators = [
            ("Salesforce Login", self.simulator.generate_sf_login_event),
            ("Salesforce API", self.simulator.generate_sf_api_event),
            ("Salesforce Data", self.simulator.generate_sf_data_event),
            ("MuleSoft Performance", self.simulator.generate_mulesoft_performance_event),
            ("MuleSoft Error", self.simulator.generate_mulesoft_error_event),
            ("MuleSoft Uptime", self.simulator.generate_mulesoft_uptime_event)
        ]

        all_passed = True

        for name, generator in generators:
            try:
                event = generator()

                # Validate required fields
                required_fields = ["eventType", "sourceSystem", "timestamp", "eventId"]
                missing_fields = [field for field in required_fields if field not in event]

                if missing_fields:
                    self.log_test(f"Event Generation {name}", "FAIL", f"Missing fields: {missing_fields}")
                    all_passed = False
                else:
                    self.log_test(f"Event Generation {name}", "PASS", f"Event ID: {event['eventId'][:8]}")

            except Exception as e:
                self.log_test(f"Event Generation {name}", "FAIL", f"Exception: {str(e)}")
                all_passed = False

        return all_passed

    def test_data_flow(self) -> bool:
        """Test complete data flow with batch events"""
        print("\n🧪 Testing Data Flow")
        print("-" * 40)

        # Send a batch of test events
        test_events = [
            ("salesforceloghandler", self.simulator.generate_sf_login_event()),
            ("salesforceloghandler", self.simulator.generate_sf_api_event()),
            ("mulesoftloghandler", self.simulator.generate_mulesoft_performance_event()),
            ("mulesoftloghandler", self.simulator.generate_mulesoft_error_event()),
            ("universalloghandler", self.simulator.generate_mulesoft_uptime_event())
        ]

        successful_sends = 0

        for endpoint, event in test_events:
            try:
                if self.simulator.send_event(event, endpoint):
                    successful_sends += 1
                time.sleep(1)  # Small delay between events
            except Exception as e:
                self.log_test("Data Flow Send", "FAIL", f"Exception: {str(e)}")

        success_rate = (successful_sends / len(test_events)) * 100

        if success_rate >= 80:
            self.log_test("Data Flow", "PASS", f"Success rate: {success_rate:.1f}% ({successful_sends}/{len(test_events)})")
            return True
        else:
            self.log_test("Data Flow", "FAIL", f"Success rate: {success_rate:.1f}% ({successful_sends}/{len(test_events)})")
            return False

    def test_performance_load(self) -> bool:
        """Test system performance under load"""
        print("\n🧪 Testing Performance Load")
        print("-" * 40)

        start_time = time.time()
        events_sent = 0
        errors = 0

        # Send 20 events rapidly
        for i in range(20):
            try:
                if i % 2 == 0:
                    event = self.simulator.generate_sf_api_event()
                    endpoint = "salesforceloghandler"
                else:
                    event = self.simulator.generate_mulesoft_performance_event()
                    endpoint = "mulesoftloghandler"

                if self.simulator.send_event(event, endpoint):
                    events_sent += 1
                else:
                    errors += 1

            except Exception:
                errors += 1

        end_time = time.time()
        duration = end_time - start_time
        events_per_second = events_sent / duration if duration > 0 else 0

        if events_per_second >= 5 and errors <= 2:
            self.log_test("Performance Load", "PASS", f"Rate: {events_per_second:.1f} events/sec, Errors: {errors}")
            return True
        else:
            self.log_test("Performance Load", "FAIL", f"Rate: {events_per_second:.1f} events/sec, Errors: {errors}")
            return False

    def test_error_handling(self) -> bool:
        """Test error handling with invalid data"""
        print("\n🧪 Testing Error Handling")
        print("-" * 40)

        # Test invalid JSON
        try:
            url = f"{self.function_base_url}/api/salesforceloghandler"
            response = requests.post(
                url,
                data="invalid json",
                timeout=10,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 400:
                self.log_test("Invalid JSON Handling", "PASS", f"Correctly returned 400")
            else:
                self.log_test("Invalid JSON Handling", "FAIL", f"Expected 400, got {response.status_code}")
                return False

        except Exception as e:
            self.log_test("Invalid JSON Handling", "FAIL", f"Exception: {str(e)}")
            return False

        # Test empty payload
        try:
            response = requests.post(
                url,
                json={},
                timeout=10,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code in [200, 400]:  # Either should be acceptable
                self.log_test("Empty Payload Handling", "PASS", f"Status: {response.status_code}")
            else:
                self.log_test("Empty Payload Handling", "FAIL", f"Unexpected status: {response.status_code}")
                return False

        except Exception as e:
            self.log_test("Empty Payload Handling", "FAIL", f"Exception: {str(e)}")
            return False

        return True

    def generate_dashboard_test_data(self) -> bool:
        """Generate comprehensive test data for dashboard validation"""
        print("\n🧪 Generating Dashboard Test Data")
        print("-" * 40)

        # Generate diverse events for dashboard testing
        events_to_generate = [
            # Salesforce events with varying response times
            ("salesforceloghandler", lambda: {**self.simulator.generate_sf_api_event(), "ResponseTime_d": 150}),
            ("salesforceloghandler", lambda: {**self.simulator.generate_sf_api_event(), "ResponseTime_d": 300}),
            ("salesforceloghandler", lambda: {**self.simulator.generate_sf_api_event(), "ResponseTime_d": 500}),

            # MuleSoft performance events
            ("mulesoftloghandler", self.simulator.generate_mulesoft_performance_event),
            ("mulesoftloghandler", self.simulator.generate_mulesoft_performance_event),

            # MuleSoft error events
            ("mulesoftloghandler", self.simulator.generate_mulesoft_error_event),
            ("mulesoftloghandler", self.simulator.generate_mulesoft_error_event),

            # MuleSoft uptime events
            ("mulesoftloghandler", self.simulator.generate_mulesoft_uptime_event),
        ]

        successful = 0

        for endpoint, generator in events_to_generate:
            try:
                event = generator()
                if self.simulator.send_event(event, endpoint):
                    successful += 1
                time.sleep(0.5)  # Small delay
            except Exception as e:
                print(f"   Error generating event: {str(e)}")

        success_rate = (successful / len(events_to_generate)) * 100

        if success_rate >= 75:
            self.log_test("Dashboard Test Data", "PASS", f"Generated {successful}/{len(events_to_generate)} events")
            return True
        else:
            self.log_test("Dashboard Test Data", "FAIL", f"Only generated {successful}/{len(events_to_generate)} events")
            return False

    def run_all_tests(self) -> Dict:
        """Run all tests and return summary"""
        print("🚀 Starting Comprehensive Pipeline Tests")
        print("=" * 60)

        tests = [
            ("Function Endpoints", self.test_function_endpoints),
            ("Event Generation", self.test_event_generation),
            ("Data Flow", self.test_data_flow),
            ("Performance Load", self.test_performance_load),
            ("Error Handling", self.test_error_handling),
            ("Dashboard Test Data", self.generate_dashboard_test_data)
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log_test(test_name, "FAIL", f"Test exception: {str(e)}")
                failed += 1

        # Summary
        print("\n" + "=" * 60)
        print("🏁 Test Summary")
        print("=" * 60)
        print(f"Total Tests: {passed + failed}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/(passed+failed)*100):.1f}%")

        if failed == 0:
            print("🎉 All tests passed! Pipeline is fully functional.")
        elif failed <= 2:
            print("⚠️ Most tests passed. Minor issues detected.")
        else:
            print("❌ Multiple test failures. Pipeline needs attention.")

        return {
            "total": passed + failed,
            "passed": passed,
            "failed": failed,
            "success_rate": (passed/(passed+failed)*100) if (passed+failed) > 0 else 0,
            "results": self.test_results
        }

def main():
    """Main test execution"""
    print("🔧 Comprehensive API Monitoring Pipeline Test")
    print("=" * 60)

    # Configuration
    function_url = "https://azurepoc-function-app.azurewebsites.net"
    workspace_id = "7208379a-ae11-4c06-bb1c-a8fc4d0c34b4"

    print(f"Function URL: {function_url}")
    print(f"Workspace ID: {workspace_id}")

    # Run tests
    test_suite = PipelineTestSuite(function_url, workspace_id)
    results = test_suite.run_all_tests()

    # Save results
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Detailed results saved to: test_results.json")

    # Dashboard verification instructions
    print("\n🔍 Manual Dashboard Verification Steps:")
    print("-" * 40)
    print("1. Go to Azure Portal → Log Analytics Workspaces")
    print("2. Select 'azurepoc-workspace'")
    print("3. Go to 'Logs' and run these queries:")
    print()
    print("   // Check recent events")
    print("   union SalesforceEvent_CL, MuleSoftPerformance_CL, MuleSoftError_CL, MuleSoftUptime_CL")
    print("   | where TimeGenerated > ago(1h)")
    print("   | summarize count() by Type")
    print()
    print("4. Go to Dashboards → 'azurepoc-api-dashboard'")
    print("5. Verify the 2 key metrics are displaying data:")
    print("   - API Response Times")
    print("   - API Error Rates")

if __name__ == "__main__":
    main()