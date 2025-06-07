#!/usr/bin/env python3
"""
Salesforce Event Simulator
Generates mock Salesforce events and sends them to Azure Function App
"""

import json
import time
import random
import requests
from datetime import datetime, timedelta
from typing import Dict, List
import uuid

class SalesforceEventSimulator:
    def __init__(self, function_url: str):
        self.function_url = function_url
        self.session = requests.Session()

        # Sample data for realistic events
        self.users = [
            "john.doe@company.com", "jane.smith@company.com", "admin@company.com",
            "sales.rep@company.com", "manager@company.com", "developer@company.com"
        ]

        self.api_endpoints = [
            "/services/data/v58.0/sobjects/Account/",
            "/services/data/v58.0/sobjects/Contact/",
            "/services/data/v58.0/sobjects/Opportunity/",
            "/services/data/v58.0/query/",
            "/services/apexrest/CustomAPI/"
        ]

        self.countries = ["US", "UK", "DE", "FR", "CA", "AU", "JP"]
        self.browsers = ["Chrome", "Firefox", "Safari", "Edge"]

    def generate_login_event(self) -> Dict:
        """Generate a mock Salesforce login event"""
        user = random.choice(self.users)
        success = random.choice([True, True, True, False])  # 75% success rate

        event = {
            "eventType": "Login",
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

    def generate_api_event(self) -> Dict:
        """Generate a mock Salesforce API usage event"""
        user = random.choice(self.users)
        endpoint = random.choice(self.api_endpoints)
        method = random.choice(["GET", "POST", "PUT", "DELETE", "PATCH"])
        status_code = random.choices([200, 201, 400, 401, 403, 404, 500],
                                   weights=[60, 15, 10, 5, 3, 4, 3])[0]

        event = {
            "eventType": "API_Usage",
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

    def generate_data_event(self) -> Dict:
        """Generate a mock Salesforce data modification event"""
        user = random.choice(self.users)
        objects = ["Account", "Contact", "Opportunity", "Lead", "Case"]
        actions = ["Create", "Update", "Delete", "View"]

        event = {
            "eventType": "Data_Modification",
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

    def send_event(self, event: Dict) -> bool:
        """Send an event to the Azure Function"""
        try:
            response = self.session.post(
                self.function_url,
                json=event,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                print(f"✅ Sent {event['eventType']} event - {event['eventId'][:8]}")
                return True
            else:
                print(f"❌ Failed to send event: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Network error sending event: {str(e)}")
            return False

    def run_simulation(self, duration_minutes: int = 5, events_per_minute: int = 6):
        """Run the simulation for specified duration"""
        print(f"🚀 Starting Salesforce Event Simulation")
        print(f"   Duration: {duration_minutes} minutes")
        print(f"   Rate: {events_per_minute} events/minute")
        print(f"   Target: {self.function_url}")
        print("-" * 50)

        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        event_count = 0
        success_count = 0

        while datetime.now() < end_time:
            # Generate random event type
            event_generators = [
                self.generate_login_event,
                self.generate_api_event,
                self.generate_data_event
            ]

            # Weight towards API events (most common)
            generator = random.choices(
                event_generators,
                weights=[20, 60, 20]  # API events are most common
            )[0]

            event = generator()

            if self.send_event(event):
                success_count += 1

            event_count += 1

            # Wait before next event
            time.sleep(60 / events_per_minute)

        print("-" * 50)
        print(f"🏁 Simulation Complete!")
        print(f"   Total Events: {event_count}")
        print(f"   Successful: {success_count}")
        print(f"   Failed: {event_count - success_count}")
        print(f"   Success Rate: {(success_count/event_count*100):.1f}%")

def main():
    """Main function to run the simulator"""

    # You'll need to update this URL after deploying your Function App
    # Format: https://<function-app-name>.azurewebsites.net/api/salesforceLogHandler
    function_url = input("Enter your Function App URL (or press Enter for default): ").strip()

    if not function_url:
        function_url = "https://azurepoc-function-app.azurewebsites.net/api/salesforceLogHandler"
        print(f"Using default URL: {function_url}")

    simulator = SalesforceEventSimulator(function_url)

    # Test single event first
    print("🧪 Testing with a single event...")
    test_event = simulator.generate_login_event()
    if simulator.send_event(test_event):
        print("✅ Single event test successful!")

        # Ask user for simulation parameters
        try:
            duration = int(input("Enter simulation duration in minutes (default 2): ") or "2")
            rate = int(input("Enter events per minute (default 6): ") or "6")
        except ValueError:
            duration, rate = 2, 6

        simulator.run_simulation(duration, rate)
    else:
        print("❌ Single event test failed. Check your Function App URL and deployment.")

if __name__ == "__main__":
    main()