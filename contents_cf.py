import requests
import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file

def list_all_zones(headers):
    url = "https://api.cloudflare.com/client/v4/zones"
    params = {"page": 1, "per_page": 50}
    zones = []

    while True:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        zones.extend(data.get("result", []))

        if not data["result_info"].get("more"):
            break

        params["page"] += 1

    return zones

def find_zone_id_for_domain(domain, zones):
    for zone in zones:
        if domain.endswith(zone["name"]):
            return zone["id"]
    raise Exception(f"Zone for domain '{domain}' not found.")

def list_dns_records(zone_id, headers, domain):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    params = {"page": 1, "per_page": 50}
    records = []

    while True:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        for record in data.get("result", []):
            if record["name"] == domain:
                records.append((record["content"], record["type"]))

        if not data["result_info"].get("more"):
            break

        params["page"] += 1

    return records

def get_dns_info(domain):
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")
    if not api_token:
        raise Exception("Missing CLOUDFLARE_API_TOKEN in .env file.")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    zones = list_all_zones(headers)
    zone_id = find_zone_id_for_domain(domain, zones)
    records = list_dns_records(zone_id, headers, domain)

    if not records:
        return f"No DNS records found for *{domain}*."

    formatted = "\n".join(
        f"*Content:* {content}, *Type:* {rtype}" for content, rtype in records
    )
    return f"*DNS Records for {domain}:*\n{formatted}"