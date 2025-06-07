#!/usr/bin/env python3
"""
Multi-API Event Simulator
Generates mock Salesforce and MuleSoft events and sends them to Azure Function App
"""

import json
import time
import random
import requests
from datetime import datetime, timedelta
from typing import Dict, List
import uuid

class MultiAPIEventSimulator:
    def __init__(self, function_base_url: str):
        self.function_base_url = function_base_url.rstrip('/')
        self.session = requests.Session()

        # Salesforce sample data
        self.sf_users = [
            "john.doe@company.com", "jane.smith@company.com", "admin@company.com",
            "sales.rep@company.com", "manager@company.com", "developer@company.com"
        ]

        self.sf_api_endpoints = [
            "/services/data/v58.0/sobjects/Account/",
            "/services/data/v58.0/sobjects/Contact/",
            "/services/data/v58.0/sobjects/Opportunity/",
            "/services/data/v58.0/query/",
            "/services/apexrest/CustomAPI/"
        ]

        # MuleSoft sample data
        self.mulesoft_apis = [
            {"name": "Customer API", "endpoint": "/api/customers", "version": "v2.1"},
            {"name": "Order API", "endpoint": "/api/orders", "version": "v1.3"},
            {"name": "Inventory API", "endpoint": "/api/inventory", "version": "v3.0"},
            {"name": "Payment API", "endpoint": "/api/payments", "version": "v2.0"},
            {"name": "Notification API", "endpoint": "/api/notifications", "version": "v1.5"}
        ]

        self.mulesoft_environments = ["DEV", "TEST", "STAGING", "PROD"]
        self.mulesoft_apps = ["retail-customer-exp", "backend-integration", "payment-processor", "data-sync"]

        self.countries = ["US", "UK", "DE", "FR", "CA", "AU", "JP"]
        self.browsers = ["Chrome", "Firefox", "Safari", "Edge"]

    # ===== SALESFORCE EVENT GENERATORS =====

    def generate_sf_login_event(self) -> Dict:
        """Generate a mock Salesforce login event"""
        user = random.choice(self.sf_users)
        success = random.choice([True, True, True, False])  # 75% success rate

        event = {
            "eventType": "Login",
            "sourceSystem": "Salesforce",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "eventId": str(uuid.uuid4()),
            "userId": user,
            "username": user,
            "loginType": random.choice(["Application", "SAML SSO", "OAuth"]),
            "sourceIp": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            "country": random.choice(self.countries),
            "browser": random.choice(self.browsers),
            "platform": random.choice(["Windows", "Mac", "Linux", "Mobile"]),
            "success": success,
            "sessionId": str(uuid.uuid4())[:8] if success else None,
            "failureReason": None if success else random.choice([
                "Invalid password", "Account locked", "MFA required", "IP restriction"
            ])
        }
        return event

    def generate_sf_api_event(self) -> Dict:
        """Generate a mock Salesforce API usage event"""
        user = random.choice(self.sf_users)
        endpoint = random.choice(self.sf_api_endpoints)
        method = random.choice(["GET", "POST", "PUT", "DELETE", "PATCH"])
        status_code = random.choices([200, 201, 400, 401, 403, 404, 500],
                                   weights=[60, 15, 10, 5, 3, 4, 3])[0]

        event = {
            "eventType": "API_Usage",
            "sourceSystem": "Salesforce",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "eventId": str(uuid.uuid4()),
            "userId": user,
            "apiEndpoint": endpoint,
            "httpMethod": method,
            "statusCode": status_code,
            "responseTime": random.randint(50, 2000),  # milliseconds
            "recordsProcessed": random.randint(1, 1000) if method == "GET" else random.randint(1, 100),
            "apiVersion": "v58.0",
            "clientApplication": random.choice(["Salesforce Mobile", "Data Loader", "Custom App", "Integration"]),
            "sourceIp": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        }
        return event

    def generate_sf_data_event(self) -> Dict:
        """Generate a mock Salesforce data modification event"""
        user = random.choice(self.sf_users)
        objects = ["Account", "Contact", "Opportunity", "Lead", "Case"]
        actions = ["Create", "Update", "Delete", "View"]

        event = {
            "eventType": "Data_Modification",
            "sourceSystem": "Salesforce",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "eventId": str(uuid.uuid4()),
            "userId": user,
            "sobjectType": random.choice(objects),
            "action": random.choice(actions),
            "recordId": f"{''.join(random.choices('0123456789ABCDEF', k=15))}",
            "fieldsModified": random.randint(1, 10),
            "oldValues": {"Status": "New", "Amount": 1000} if random.choice([True, False]) else {},
            "newValues": {"Status": "Qualified", "Amount": 1500} if random.choice([True, False]) else {}
        }
        return event

    # ===== MULESOFT EVENT GENERATORS =====

    def generate_mulesoft_performance_event(self) -> Dict:
        """Generate MuleSoft API performance/latency event"""
        api = random.choice(self.mulesoft_apis)
        env = random.choice(self.mulesoft_environments)
        app = random.choice(self.mulesoft_apps)

        # Simulate realistic latency patterns
        base_latency = random.randint(50, 200)
        if env == "PROD":
            latency = base_latency + random.randint(0, 100)
        else:
            latency = base_latency + random.randint(0, 500)

        event = {
            "eventType": "MuleSoft_Performance",
            "sourceSystem": "MuleSoft",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "eventId": str(uuid.uuid4()),
            "apiName": api["name"],
            "apiEndpoint": api["endpoint"],
            "apiVersion": api["version"],
            "environment": env,
            "applicationName": app,
            "responseTime": latency,
            "throughput": random.randint(10, 500),  # requests per minute
            "memoryUsage": round(random.uniform(40.0, 85.0), 2),  # percentage
            "cpuUsage": round(random.uniform(15.0, 75.0), 2),  # percentage
            "statusCode": random.choices([200, 201, 202], weights=[80, 15, 5])[0]
        }
        return event

    def generate_mulesoft_error_event(self) -> Dict:
        """Generate MuleSoft API error event"""
        api = random.choice(self.mulesoft_apis)
        env = random.choice(self.mulesoft_environments)
        app = random.choice(self.mulesoft_apps)

        error_codes = [400, 401, 403, 404, 429, 500, 502, 503, 504]
        error_types = [
            "CONNECTIVITY", "TIMEOUT", "SECURITY", "ROUTING",
            "TRANSFORMATION", "POLICY_VIOLATION", "RATE_LIMIT_EXCEEDED"
        ]

        status_code = random.choice(error_codes)

        event = {
            "eventType": "MuleSoft_Error",
            "sourceSystem": "MuleSoft",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "eventId": str(uuid.uuid4()),
            "apiName": api["name"],
            "apiEndpoint": api["endpoint"],
            "apiVersion": api["version"],
            "environment": env,
            "applicationName": app,
            "statusCode": status_code,
            "errorType": random.choice(error_types),
            "errorMessage": f"API error occurred: {status_code}",
            "responseTime": random.randint(1000, 10000),  # slower for errors
            "retryAttempts": random.randint(0, 3),
            "sourceIp": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        }
        return event

    def generate_mulesoft_uptime_event(self) -> Dict:
        """Generate MuleSoft uptime/availability event"""
        api = random.choice(self.mulesoft_apis)
        env = random.choice(self.mulesoft_environments)
        app = random.choice(self.mulesoft_apps)

        # Simulate uptime percentage (higher for PROD)
        if env == "PROD":
            uptime = round(random.uniform(99.0, 99.99), 3)
        else:
            uptime = round(random.uniform(95.0, 99.5), 3)

        event = {
            "eventType": "MuleSoft_Uptime",
            "sourceSystem": "MuleSoft",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "eventId": str(uuid.uuid4()),
            "apiName": api["name"],
            "apiEndpoint": api["endpoint"],
            "apiVersion": api["version"],
            "environment": env,
            "applicationName": app,
            "availability": uptime,
            "uptime": uptime,
            "totalRequests": random.randint(1000, 50000),
            "successfulRequests": random.randint(950, 49500),
            "failedRequests": random.randint(0, 500),
            "avgResponseTime": random.randint(80, 300),
            "monitoringPeriod": "1h"  # 1 hour monitoring window
        }
        return event

    # ===== SENDING LOGIC =====

    def send_event(self, event: Dict, endpoint: str = "universalLogHandler") -> bool:
        """Send event to Azure Function"""
        try:
            # Convert endpoint to lowercase to match Azure Functions URL format
            endpoint_lower = endpoint.lower()
            url = f"{self.function_base_url}/api/{endpoint_lower}"

            response = requests.post(
                url,
                json=event,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                print(f"✅ Successfully sent {event['eventType']} event to {endpoint}")
                return True
            else:
                print(f"❌ Failed to send event: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error sending event: {str(e)}")
            return False

    def run_simulation(self, duration_minutes: int = 5, events_per_minute: int = 6):
        """Run the simulation for specified duration with mixed event types"""
        print(f"🚀 Starting Multi-API Event Simulation")
        print(f"   Duration: {duration_minutes} minutes")
        print(f"   Rate: {events_per_minute} events/minute")
        print(f"   Target: {self.function_base_url}")
        print("   Event Types: Salesforce + MuleSoft")
        print("-" * 60)

        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        event_count = 0
        success_count = 0
        event_types = {'Salesforce': 0, 'MuleSoft': 0}

        while datetime.now() < end_time:
            # Generate random event type (40% Salesforce, 60% MuleSoft)
            if random.random() < 0.4:  # Salesforce event
                event_generators = [
                    self.generate_sf_login_event,
                    self.generate_sf_api_event,
                    self.generate_sf_data_event
                ]
                generator = random.choices(event_generators, weights=[20, 60, 20])[0]
                endpoint = "salesforceloghandler"
                event_types['Salesforce'] += 1
            else:  # MuleSoft event
                event_generators = [
                    self.generate_mulesoft_performance_event,
                    self.generate_mulesoft_error_event,
                    self.generate_mulesoft_uptime_event
                ]
                generator = random.choices(event_generators, weights=[60, 25, 15])[0]
                endpoint = "mulesoftloghandler"
                event_types['MuleSoft'] += 1

            event = generator()

            if self.send_event(event, endpoint):
                success_count += 1

            event_count += 1

            # Wait before next event
            time.sleep(60 / events_per_minute)

        print("-" * 60)
        print(f"🏁 Simulation Complete!")
        print(f"   Total Events: {event_count}")
        print(f"   Successful: {success_count}")
        print(f"   Failed: {event_count - success_count}")
        print(f"   Success Rate: {(success_count/event_count*100):.1f}%")
        print(f"   Salesforce Events: {event_types['Salesforce']}")
        print(f"   MuleSoft Events: {event_types['MuleSoft']}")

def main():
    """Main function to run the simulator"""

    print("🔧 Multi-API Event Simulator")
    print("Supports: Salesforce + MuleSoft events")
    print("-" * 40)

    # Function App base URL
    function_url = input("Enter your Function App base URL (or press Enter for default): ").strip()

    if not function_url:
        function_url = "https://azurepoc-function-app.azurewebsites.net"
        print(f"Using default URL: {function_url}")

    simulator = MultiAPIEventSimulator(function_url)

    # Test single events first
    print("\n🧪 Testing with sample events...")

    # Test Salesforce event
    sf_test = simulator.generate_sf_login_event()
    sf_success = simulator.send_event(sf_test, "salesforceLogHandler")

    # Test MuleSoft event
    ms_test = simulator.generate_mulesoft_performance_event()
    ms_success = simulator.send_event(ms_test, "mulesoftLogHandler")

    if sf_success and ms_success:
        print("✅ Both event types tested successfully!")

        # Ask user for simulation parameters
        try:
            duration = int(input("\nEnter simulation duration in minutes (default 3): ") or "3")
            rate = int(input("Enter events per minute (default 8): ") or "8")
        except ValueError:
            duration, rate = 3, 8

        simulator.run_simulation(duration, rate)
    else:
        print("❌ Event tests failed. Check your Function App URL and deployment.")
        if not sf_success:
            print("  - Salesforce event failed")
        if not ms_success:
            print("  - MuleSoft event failed")

if __name__ == "__main__":
    main()