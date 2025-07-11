from flask import request, Response
import re, os, requests

RAY_ID_REGEX = re.compile(r"^[a-fA-F0-9]{16}$")

def handle_cf_ray(client):
    data = request.form
    channel_id = data.get('channel_id')
    text = data.get('text')

    args = text.strip().split()

    if len(args) != 2 or args[0] != "-ray":
        return Response("Usage: /cf -ray [ray_id] or /cloudflare -ray [ray_id]", status=200)

    ray_id = args[1]

    if not RAY_ID_REGEX.fullmatch(ray_id):
        return Response("Invalid Ray ID format. A Ray ID is a 16-character hex string.", status=200)

    # Cloudflare API setup
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")
    zone_tag = os.getenv("CLOUDFLARE_ZONE_ID")  # This is the zone ID

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
              }
            }
          }
        }
        """,
        "variables": {
            "zoneTag": zone_tag,
            "filter": {
                "rayName": ray_id,
                # datetime window
                "datetime_geq": "2025-07-01T00:00:00Z",
                "datetime_leq": "2025-07-10T23:59:59Z"
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    res = requests.post(url, json=query, headers=headers)

    if not res.ok:
        return Response(f"Error fetching data: {res.status_code} {res.text}", status=200)

    data = res.json()
    events = data.get("data", {}).get("viewer", {}).get("zones", [{}])[0].get("firewallEventsAdaptive", [])

    # checks whether GraphQL request is succeeding or
    # getting results but missing them in the parsing logic
    print("DEBUG: GraphQL response:", data)
    if not events:
        return Response("No firewall events found for that Ray ID.", status=200)

    event = events[0]

    msg = (
        f"*Ray ID:* `{ray_id}`\n"
        f"*Action:* {event.get('action')}\n"
        f"*IP:* {event.get('clientIP')} ({event.get('clientCountryName')})\n"
        f"*ASN:* {event.get('clientAsn')}\n"
        f"*Path:* `{event.get('clientRequestPath')}?{event.get('clientRequestQuery')}`\n"
        f"*Source:* {event.get('source')}\n"
        f"*User Agent:* `{event.get('userAgent')}`\n"
        f"*Datetime:* {event.get('datetime')}\n"
    )

    client.chat_postMessage(channel=channel_id, text=msg)
    return Response(), 200
