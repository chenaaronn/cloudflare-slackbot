# /cf -ray [ray_id] [domain]
import os
import re
import requests
from flask import request, Response

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
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
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

def get_security_event(zone_id, ray_id, headers):
    """Fetches the security event for a given Zone ID and Ray ID with pagination."""
    page = 1
    per_page = 50  # You can increase to 1000 if needed

    while True:
        try:
            response = requests.get(
                f"{CF_API_BASE_URL}/zones/{zone_id}/security/events",
                headers=headers,
                params={
                    "ray_id": ray_id,
                    "page": page,
                    "per_page": per_page
                }
            )
            response.raise_for_status()
            data = response.json()
            events = data.get("result", [])
            for event in events:
                if event.get("ray_id") == ray_id:
                    return event

            # Pagination logic
            result_info = data.get("result_info", {})
            total_pages = result_info.get("total_pages", 1)
            if page >= total_pages:
                break
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching security event: {e}")
            return None

    return None  # Ray ID not found

def handle_cf_ray(client):
    """
    Handles the /cf slash command to look up a Cloudflare Ray ID.
    Expected format: /cf -ray [ray_id] [domain]
    """
    data = request.form
    channel_id = data.get('channel_id')
    text = data.get('text')
    
    # --- 1. Argument Parsing and Validation ---
    args = text.strip().split()
    if len(args) != 3 or args[0] != "-ray":
        usage_text = "Usage: `/cf -ray [ray_id] [domain]` (e.g., `/cf -ray 783dd7324ebfbb62 example.com`)"
        return Response(usage_text, status=200)

    ray_id = args[1]
    domain = args[2]

    if not RAY_ID_REGEX.fullmatch(ray_id):
        error_msg = "Invalid Ray ID format. A Ray ID is a 16-character hex string (e.g., 783dd7324ebfbb62)."
        return Response(error_msg, status=200)
    
    # --- 2. API Authentication ---
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not api_token:
        error_msg = "Administrator error: `CLOUDFLARE_API_TOKEN` is not configured."
        # Post the message to the channel so the user sees it
        client.chat_postMessage(channel=channel_id, text=error_msg)
        return Response(), 200

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    # --- 3. Fetch Data from Cloudflare API ---
    # Post an initial message to let the user know we're working on it
    client.chat_postMessage(channel=channel_id, text=f"🔍 Looking up Ray ID `{ray_id}` for `{domain}`...")

    zone_id = get_zone_id(domain, headers)
    if not zone_id:
        error_msg = f"Could not find a Cloudflare zone for the domain `{domain}`. Please check the domain name."
        client.chat_postMessage(channel=channel_id, text=error_msg)
        return Response(), 200
    
    event = get_security_event(zone_id, ray_id, headers)
    if not event:
        error_msg = f"Could not find a security event for Ray ID `{ray_id}` in `{domain}`. The event might be too old or the ID is incorrect."
        client.chat_postMessage(channel=channel_id, text=error_msg)
        return Response(), 200

    # --- 4. Format and Send the Response ---
    # Safely get values from the event dictionary using .get() to avoid errors if a key is missing
    response_msg = (
        f"✅ *Found Event for Ray ID:* `{event.get('ray_id', ray_id)}`\n\n"
        f"*Domain:* `{domain}`\n"
        f"*Service:* `{event.get('source', 'N/A')}`\n"
        f"*Action Taken:* `{event.get('action', 'N/A')}`\n"
        f"*IP Address:* `{event.get('ip', 'N/A')}`\n"
        f"*Country:* `{event.get('ip_location', {}).get('country', 'N/A')}`\n"
        f"*Ruleset:* `{event.get('ruleset_name', 'N/A')}`\n"
        f"*Rule:* `{event.get('rule_id', 'N/A')}`\n"
        f"*Triggered At:* `{event.get('occurred_at', 'N/A')}`"
    )

    client.chat_postMessage(channel=channel_id, text=response_msg)
    return Response(), 200
