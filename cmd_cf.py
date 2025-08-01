import re, os, requests
from datetime import datetime, timedelta, timezone

RAY_ID_REGEX = re.compile(r"^[a-fA-F0-9]{16}$")

def handle_cf_ray(client, channel_id, text):
    args = text.strip().split()

    if len(args) != 2 or args[0] != "-ray":
        client.chat_postMessage(
            channel=channel_id,
            text="Usage: /cf -ray [ray_id] or /cloudflare -ray [ray_id]"
        )
        return {"statusCode": 200, "body": ""}

    ray_id = args[1]

    if not RAY_ID_REGEX.fullmatch(ray_id):
        client.chat_postMessage(
            channel=channel_id,
            text="Invalid Ray ID format. A Ray ID is a 16-character hex string."
        )
        return {"statusCode": 200, "body": ""}

    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=30)).isoformat()
    end = now.isoformat()

    api_token = os.getenv("CLOUDFLARE_API_TOKEN")
    zone_tag = os.getenv("CLOUDFLARE_ZONE_ID")

    url = "https://api.cloudflare.com/client/v4/graphql"

    query = {
        "query": """
        query ListFirewallEvents($zoneTag: string, $filter: FirewallEventsAdaptiveFilter_InputObject) {
          viewer {
            zones(filter: { zoneTag: $zoneTag }) {
              firewallEventsAdaptive(
                filter: $filter
                limit: 1
                orderBy: [datetime_DESC]
              ) {
                action
                clientAsn
                clientCountryName
                clientIP
                clientRequestPath
                clientRequestQuery
                datetime
                source
                userAgent
                
                botScore
                botScoreSrcName
                ja3Hash
                ja4

                clientRequestHTTPHost
              }
            }
          }
        }
        """,
        "variables": {
            "zoneTag": zone_tag,
            "filter": {
                "rayName": ray_id,
                "datetime_geq": start,
                "datetime_leq": end
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    res = requests.post(url, json=query, headers=headers)

    if not res.ok:
        client.chat_postMessage(channel=channel_id, text=f"Error fetching data: {res.status_code} {res.text}")
        return {"statusCode": 200, "body": ""}

    try:
        data = res.json()
    except ValueError:
        client.chat_postMessage(channel=channel_id, text=f"Non-JSON response received: {res.text}")
        return {"statusCode": 200, "body": ""}

    if data.get("errors"):
        client.chat_postMessage(channel=channel_id, text=f"GraphQL error: {data['errors'][0]['message']}")
        return {"statusCode": 200, "body": ""}

    events = data.get("data", {}).get("viewer", {}).get("zones", [{}])[0].get("firewallEventsAdaptive", [])

    if not events:
        client.chat_postMessage(channel=channel_id, text="No firewall events found for that Ray ID.")
        return {"statusCode": 200, "body": ""}

    event = events[0]

    msg = (
        f"*Ray ID:* `{ray_id}`\n"
        f"*Datetime:* {event.get('datetime')}\n"
        f"*Host:* {event.get('clientRequestHTTPHost')}\n"
        f"*Path:* `{event.get('clientRequestPath')}?{event.get('clientRequestQuery')}`\n"

        f"\n_Firewall Details:_\n"
        f"*Action:* {event.get('action')}\n"
        f"*Source:* {event.get('source')}\n"

        f"\n_Bot Management:_\n"
        f"*Bot Score:* {event.get('botScore')}\n"  
        f"*Bot Score Source:* {event.get('botScoreSrcName')}\n"
        f"*JA3 Fingerprint:* {event.get('ja3Hash')}\n"
        f"*JA4 Fingerprint:* {event.get('ja4')}\n"
        
        f"\n_Client Details:_\n"
        f"*IP:* {event.get('clientIP')} ({event.get('clientCountryName')})\n"
        f"*ASN:* {event.get('clientAsn')}\n"
        f"*User Agent:* `{event.get('userAgent')}`\n"
    )

    client.chat_postMessage(channel=channel_id, text=msg)
    return {"statusCode": 200, "body": ""}
# handle_cf_ray()
