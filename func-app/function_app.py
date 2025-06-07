import os
import json
import datetime
import hashlib
import hmac
import base64
import logging

import requests
import azure.functions as func

# Pull from your Function App's app_settings (wired in Terraform)
WS_ID  = os.environ.get("LOG_ANALYTICS_WORKSPACE_ID")
WS_KEY = os.environ.get("LOG_ANALYTICS_PRIMARY_KEY")

def post_to_law(body: dict, log_type: str):
    """Send a single JSON object into the LA workspace as <log_type>_CL."""
    if not WS_ID or not WS_KEY:
        logging.error("Missing LOG_ANALYTICS_WORKSPACE_ID or LOG_ANALYTICS_PRIMARY_KEY")
        return 500, "Missing workspace configuration"

    body_json = json.dumps(body)
    ts = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    string_to_hash = (
        f"POST\n"
        f"{len(body_json)}\n"
        f"application/json\n"
        f"x-ms-date:{ts}\n"
        f"/api/logs"
    )
    decoded_key = base64.b64decode(WS_KEY)
    signature   = base64.b64encode(
        hmac.new(decoded_key, string_to_hash.encode("utf-8"), hashlib.sha256).digest()
    ).decode()

    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"SharedKey {WS_ID}:{signature}",
        "Log-Type":      log_type,
        "x-ms-date":     ts
    }
    url = f"https://{WS_ID}.ods.opinsights.azure.com/api/logs?api-version=2016-04-01"

    try:
        resp = requests.post(url, data=body_json, headers=headers, timeout=10)
        logging.info(f"Log Analytics response: {resp.status_code} for {log_type}")
        return resp.status_code, resp.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error posting to Log Analytics: {str(e)}")
        return 500, f"Error posting to Log Analytics: {str(e)}"

def determine_log_type(event_data: dict) -> str:
    """Determine the appropriate log type based on event content."""
    event_type = event_data.get('eventType', '')
    source_system = event_data.get('sourceSystem', '').lower()

    # MuleSoft events
    if source_system == 'mulesoft' or event_type.startswith('MuleSoft'):
        if 'latency' in event_data or 'responseTime' in event_data:
            return 'MuleSoftPerformance'
        elif 'error' in event_data or event_data.get('statusCode', 0) >= 400:
            return 'MuleSoftError'
        elif 'uptime' in event_data or 'availability' in event_data:
            return 'MuleSoftUptime'
        else:
            return 'MuleSoftGeneral'

    # Salesforce events (existing)
    elif 'salesforce' in source_system or event_type in ['Login', 'API_Usage', 'Data_Modification']:
        return 'SalesforceEvent'

    # Default fallback
    else:
        return 'GeneralEvent'

app = func.FunctionApp()

@app.route(route="salesforceLogHandler", auth_level=func.AuthLevel.ANONYMOUS)
def salesforceLogHandler(req: func.HttpRequest) -> func.HttpResponse:
    """Legacy endpoint for Salesforce events - maintains backward compatibility"""
    logging.info("▶ salesforceLogHandler invoked")

    try:
        payload = req.get_json()
        if not payload:
            return func.HttpResponse("Empty or invalid JSON payload", status_code=400)

        logging.info(f"Received Salesforce payload: {json.dumps(payload)}")

    except ValueError as e:
        logging.error(f"JSON parsing error: {str(e)}")
        return func.HttpResponse("Invalid JSON", status_code=400)

    # Add timestamp and source system if not present
    if 'timestamp' not in payload:
        payload['timestamp'] = datetime.datetime.utcnow().isoformat()
    if 'sourceSystem' not in payload:
        payload['sourceSystem'] = 'Salesforce'

    code, text = post_to_law(payload, "SalesforceEvent")

    if code == 200:
        logging.info("Successfully sent Salesforce event to Log Analytics")
        return func.HttpResponse(f"Salesforce event logged successfully: {text}", status_code=200)
    else:
        logging.error(f"Failed to send Salesforce event: {code} - {text}")
        return func.HttpResponse(f"Failed to log Salesforce event: {text}", status_code=code)

@app.route(route="mulesoftLogHandler", auth_level=func.AuthLevel.ANONYMOUS)
def mulesoftLogHandler(req: func.HttpRequest) -> func.HttpResponse:
    """Dedicated endpoint for MuleSoft events"""
    logging.info("▶ mulesoftLogHandler invoked")

    try:
        payload = req.get_json()
        if not payload:
            return func.HttpResponse("Empty or invalid JSON payload", status_code=400)

        logging.info(f"Received MuleSoft payload: {json.dumps(payload)}")

    except ValueError as e:
        logging.error(f"JSON parsing error: {str(e)}")
        return func.HttpResponse("Invalid JSON", status_code=400)

    # Add timestamp and source system if not present
    if 'timestamp' not in payload:
        payload['timestamp'] = datetime.datetime.utcnow().isoformat()
    if 'sourceSystem' not in payload:
        payload['sourceSystem'] = 'MuleSoft'

    # Determine specific log type for MuleSoft
    log_type = determine_log_type(payload)

    code, text = post_to_law(payload, log_type)

    if code == 200:
        logging.info(f"Successfully sent MuleSoft event to Log Analytics ({log_type})")
        return func.HttpResponse(f"MuleSoft event logged successfully to {log_type}: {text}", status_code=200)
    else:
        logging.error(f"Failed to send MuleSoft event: {code} - {text}")
        return func.HttpResponse(f"Failed to log MuleSoft event: {text}", status_code=code)

@app.route(route="universalLogHandler", auth_level=func.AuthLevel.ANONYMOUS)
def universalLogHandler(req: func.HttpRequest) -> func.HttpResponse:
    """Universal endpoint that can handle any event type and route appropriately"""
    logging.info("▶ universalLogHandler invoked")

    try:
        payload = req.get_json()
        if not payload:
            return func.HttpResponse("Empty or invalid JSON payload", status_code=400)

        logging.info(f"Received universal payload: {json.dumps(payload)}")

    except ValueError as e:
        logging.error(f"JSON parsing error: {str(e)}")
        return func.HttpResponse("Invalid JSON", status_code=400)

    # Add timestamp if not present
    if 'timestamp' not in payload:
        payload['timestamp'] = datetime.datetime.utcnow().isoformat()

    # Determine the appropriate log type
    log_type = determine_log_type(payload)

    code, text = post_to_law(payload, log_type)

    if code == 200:
        logging.info(f"Successfully sent event to Log Analytics ({log_type})")
        return func.HttpResponse(f"Event logged successfully to {log_type}: {text}", status_code=200)
    else:
        logging.error(f"Failed to send event: {code} - {text}")
        return func.HttpResponse(f"Failed to log event: {text}", status_code=code)
