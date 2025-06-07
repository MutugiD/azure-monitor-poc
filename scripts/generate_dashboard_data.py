#!/usr/bin/env python3
"""
Dashboard Test Data Generator
Generates comprehensive test data specifically for dashboard visualization
"""

import sys
import os
import time
import json
from datetime import datetime, timedelta
import random
import uuid

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from api_simulator import MultiAPIEventSimulator

def generate_response_time_data(simulator):
    """Generate events with varying response times for response time dashboard"""
    print("📊 Generating Response Time Test Data...")

    events_generated = 0

    # Salesforce events with different response time patterns
    salesforce_scenarios = [
        # Fast responses (good performance)
        (100, 200, 10),  # 100-200ms, 10 events
        (150, 300, 15),  # 150-300ms, 15 events
        # Normal responses
        (250, 500, 20),  # 250-500ms, 20 events
        # Slower responses (performance issues)
        (500, 1000, 10), # 500-1000ms, 10 events
        (1000, 2000, 5)  # 1000-2000ms, 5 events (outliers)
    ]

    for min_time, max_time, count in salesforce_scenarios:
        for _ in range(count):
            event = simulator.generate_sf_api_event()
            event['ResponseTime_d'] = random.randint(min_time, max_time)
            event['responseTime'] = event['ResponseTime_d']  # Backup field
            simulator.send_event(event, "salesforceloghandler")
            events_generated += 1
            time.sleep(0.2)  # Small delay

    # MuleSoft events with performance patterns
    mulesoft_scenarios = [
        # Fast integration responses
        (80, 150, 12),   # 80-150ms, 12 events
        (120, 250, 18),  # 120-250ms, 18 events
        # Normal integration responses
        (200, 400, 25),  # 200-400ms, 25 events
        # Slower integration responses
        (400, 800, 12),  # 400-800ms, 12 events
        (800, 1500, 8)   # 800-1500ms, 8 events
    ]

    for min_time, max_time, count in mulesoft_scenarios:
        for _ in range(count):
            event = simulator.generate_mulesoft_performance_event()
            event['responseTime'] = random.randint(min_time, max_time)
            event['ResponseTime_d'] = event['responseTime']  # Backup field
            simulator.send_event(event, "mulesoftloghandler")
            events_generated += 1
            time.sleep(0.2)  # Small delay

    print(f"✅ Generated {events_generated} response time events")
    return events_generated

def generate_error_rate_data(simulator):
    """Generate events with error patterns for error rate dashboard"""
    print("🚨 Generating Error Rate Test Data...")

    events_generated = 0

    # Salesforce success and error patterns
    # Generate 80% success, 20% errors for Salesforce
    for _ in range(40):  # 40 total Salesforce events
        event = simulator.generate_sf_api_event()

        if random.random() < 0.8:  # 80% success
            event['statusCode'] = random.choices([200, 201, 204], weights=[70, 20, 10])[0]
            event['success'] = True
        else:  # 20% errors
            event['statusCode'] = random.choices([400, 401, 403, 404, 429, 500, 502, 503],
                                               weights=[25, 15, 10, 15, 10, 10, 10, 5])[0]
            event['success'] = False

        event['StatusCode_d'] = event['statusCode']
        event['Success_b'] = event['success']

        simulator.send_event(event, "salesforceloghandler")
        events_generated += 1
        time.sleep(0.1)

    # MuleSoft success and error patterns
    # Generate 85% success, 15% errors for MuleSoft
    for _ in range(30):  # 30 MuleSoft performance events
        event = simulator.generate_mulesoft_performance_event()

        if random.random() < 0.85:  # 85% success
            event['statusCode'] = random.choices([200, 201, 202], weights=[80, 15, 5])[0]
            event['success'] = True
        else:  # 15% errors
            event['statusCode'] = random.choices([400, 401, 500, 502, 503, 504],
                                               weights=[20, 15, 25, 15, 15, 10])[0]
            event['success'] = False

        event['StatusCode_d'] = event['statusCode']
        event['Success_b'] = event['success']

        simulator.send_event(event, "mulesoftloghandler")
        events_generated += 1
        time.sleep(0.1)

    # Generate dedicated MuleSoft error events
    for _ in range(15):  # 15 explicit error events
        event = simulator.generate_mulesoft_error_event()
        simulator.send_event(event, "mulesoftloghandler")
        events_generated += 1
        time.sleep(0.1)

    print(f"✅ Generated {events_generated} error rate events")
    return events_generated

def generate_time_series_data(simulator):
    """Generate events spread over time for time-series dashboard testing"""
    print("📈 Generating Time-Series Data...")

    events_generated = 0

    # Generate events for the last few hours (simulated)
    base_time = datetime.utcnow()

    for hour_offset in range(-4, 1):  # Last 4 hours + current
        for _ in range(15):  # 15 events per hour
            # Alternate between systems
            if random.random() < 0.6:  # 60% MuleSoft, 40% Salesforce
                event = simulator.generate_mulesoft_performance_event()
                endpoint = "mulesoftloghandler"
            else:
                event = simulator.generate_sf_api_event()
                endpoint = "salesforceloghandler"

            # Adjust timestamp to simulate historical data
            event_time = base_time + timedelta(hours=hour_offset, minutes=random.randint(0, 59))
            event['timestamp'] = event_time.isoformat() + "Z"

            # Add response time data
            event['responseTime'] = random.randint(100, 800)
            event['ResponseTime_d'] = event['responseTime']

            # Add status codes with realistic distribution
            if random.random() < 0.9:  # 90% success
                event['statusCode'] = 200
                event['success'] = True
            else:  # 10% errors
                event['statusCode'] = random.choice([400, 500, 502, 503])
                event['success'] = False

            event['StatusCode_d'] = event['statusCode']
            event['Success_b'] = event['success']

            simulator.send_event(event, endpoint)
            events_generated += 1
            time.sleep(0.05)  # Very small delay

    print(f"✅ Generated {events_generated} time-series events")
    return events_generated

def main():
    """Main dashboard data generation"""
    print("🎨 Dashboard Test Data Generator")
    print("=" * 60)

    # Initialize simulator
    function_url = "https://azurepoc-function-app.azurewebsites.net"
    simulator = MultiAPIEventSimulator(function_url)

    print(f"Target: {function_url}")
    print("Generating comprehensive dashboard test data...")
    print("-" * 60)

    total_events = 0

    try:
        # Generate different types of test data
        total_events += generate_response_time_data(simulator)
        time.sleep(2)  # Pause between generations

        total_events += generate_error_rate_data(simulator)
        time.sleep(2)  # Pause between generations

        total_events += generate_time_series_data(simulator)

        print("\n" + "=" * 60)
        print("🎉 Dashboard Data Generation Complete!")
        print("=" * 60)
        print(f"Total Events Generated: {total_events}")
        print(f"Target Systems: Salesforce + MuleSoft")
        print(f"Data Types: Response Times, Error Rates, Time Series")

        print("\n📊 Dashboard Verification:")
        print("1. Wait 5-10 minutes for data ingestion")
        print("2. Go to Azure Portal → Log Analytics Workspaces → azurepoc-workspace")
        print("3. Run this query to verify data:")
        print()
        print("   union SalesforceEvent_CL, MuleSoftPerformance_CL, MuleSoftError_CL")
        print("   | where TimeGenerated > ago(1h)")
        print("   | extend ResponseTime = coalesce(ResponseTime_d, responseTime_d)")
        print("   | extend StatusCode = coalesce(StatusCode_d, statusCode_d)")
        print("   | summarize")
        print("     TotalEvents = count(),")
        print("     AvgResponseTime = avg(ResponseTime),")
        print("     ErrorCount = countif(StatusCode >= 400)")
        print("     by SourceSystem_s")
        print()
        print("4. Check dashboards for updated metrics:")
        print("   - API Response Times (should show varying latencies)")
        print("   - API Error Rates (should show ~10-20% error rates)")

    except KeyboardInterrupt:
        print(f"\n⚠️ Generation interrupted. Generated {total_events} events so far.")
    except Exception as e:
        print(f"\n❌ Error during generation: {str(e)}")
        print(f"Generated {total_events} events before error.")

if __name__ == "__main__":
    main()