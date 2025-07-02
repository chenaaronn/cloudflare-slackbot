import os
import re
import requests
import json
from flask import request, Response
from datetime import datetime, timedelta, timezone

# Regex to validate a 16-character hex Ray ID
RAY_ID_REGEX = re.compile(r"^[a-fA-F0-9]{16}$")
# Cloudflare API base URL
CF_API_BASE_URL = "https://api.cloudflare.com/client/v4"

def get_zone_id(domain, headers):
    """Fetches the Zone ID for a given domain."""
    try:
        response = requests.get(
            f"{CF_API_BASE_URL}/zones",
            headers=headers,
            params={"name": domain}
        )
        response.raise_for_status()
        data = response.json()
        if data.get("result"):
            return data["result"][0]["id"]
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Zone ID: {e}")
        return None
    except (KeyError, IndexError):
        print("Could not parse Zone ID from API response.")
        return None

def get_ray_details_from_logs(zone_id, ray_id, headers):
    """
    Final attempt: Fetches Ray ID details using the standard Logpull API,
    searching within the last 15 minutes.
    """
    try:
        # Using the /logs/received endpoint which requires a time window
        url = f"{CF_API_BASE_URL}/zones/{zone_id}/logs/received"
        
        # Create a 15-minute time window for the search
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=15)

        # Logpull API requires RFC3339 format for timestamps.
        params = {
            "ray_id": ray_id,
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "fields": "RayID,ClientIP,ClientRequestHost,ClientRequestMethod,ClientRequestURI,EdgeResponseStatus,OriginResponseStatus,CacheCacheStatus,WAFAction,BotScore,SecurityLevelAction"
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        # This endpoint returns logs as newline-delimited JSON, not a single JSON object
        # We need to parse it line by line
        logs = response.text.strip().split('\n')
        if logs and logs[0]: # Check if there is any actual log content
             # Each line is a JSON object. We return the first one found.
            return json.loads(logs[0])
        else:
            return None # No logs found

    except requests.exceptions.RequestException as e:
        # The API might return a 4xx error with a JSON body explaining why
        try:
            error_data = e.response.json()
            print(f"Cloudflare API Error: {error_data.get('errors')}")
        except json.JSONDecodeError:
            print(f"Error fetching Ray ID from logs: {e}")
        return None
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Could not parse Ray ID log response: {e}")
        return None

def handle_cf_ray(client):
    """
    Handles the /cf slash command to look up a Cloudflare Ray ID.
    """
    data = request.form
    channel_id = data.get('channel_id')
    text = data.get('text')
    
    args = text.strip().split()
    if len(args) != 3 or args[0] != "-ray":
        usage_text = "Usage: `/cf -ray [ray_id] [domain]`"
        return Response(usage_text, status=200)

    ray_id = args[1]
    domain = args[2]

    if not RAY_ID_REGEX.fullmatch(ray_id):
        error_msg = "Invalid Ray ID format."
        return Response(error_msg, status=200)
    
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not api_token:
        error_msg = "Administrator error: `CLOUDFLARE_API_TOKEN` is not configured."
        client.chat_postMessage(channel=channel_id, text=error_msg)
        return Response(), 200

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    client.chat_postMessage(channel=channel_id, text=f"🔍 Looking up Ray ID `{ray_id}` for `{domain}`...")

    zone_id = get_zone_id(domain, headers)
    if not zone_id:
        error_msg = f"Could not find a Cloudflare zone for the domain `{domain}`."
        client.chat_postMessage(channel=channel_id, text=error_msg)
        return Response(), 200
    
    event_object = get_ray_details_from_logs(zone_id, ray_id, headers)
    
    if not event_object:
        error_msg = f"Could not find any logs for Ray ID `{ray_id}`. The event may be outside the 15-minute search window, or the API token may lack 'Logs: Read' permissions, or this feature may not be available on your plan."
        client.chat_postMessage(channel=channel_id, text=error_msg)
        return Response(), 200

    raw_json_string = json.dumps(event_object, indent=2)
    response_msg = f"✅ *Found Log Data for Ray ID:* `{ray_id}`\n\n```{raw_json_string}```"
    
    try:
        client.chat_postMessage(channel=channel_id, text=response_msg)
    except Exception as e:
        error_text = f"Could not send the data for Ray ID `{ray_id}`. The response might be too large or a Slack API error occurred: {e}"
        client.chat_postMessage(channel=channel_id, text=error_text)

    return Response(), 200