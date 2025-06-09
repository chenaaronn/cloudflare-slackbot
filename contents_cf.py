import requests 
import os
from ipwhois import IPWhois
import ipaddress
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
# list_all_zone()

def find_zone_id_for_domain(domain, zones):
    for zone in zones:
        if domain.endswith(zone["name"]):
            return zone["id"]
    raise Exception(f"Zone for domain '{domain}' not found.")
# find_zone_id()

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
# list_dns_records()

def get_provider_from_records(records):
    providers = set()
    for content, rtype in records:
        if rtype not in ("A", "AAAA"):
            continue  # Skip non-IP records
        try:
            ip_obj = ipaddress.ip_address(content)
            res = IPWhois(str(ip_obj)).lookup_rdap()
            org = res.get('network', {}).get('name', 'Unknown')
            providers.add(org)
        except Exception:
            continue
    return ", ".join(sorted(providers)) if providers else "NA"
# get_provider()

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

    lines = [f" • Content: {content}, Type: {rtype}" for content, rtype in records]
    provider = get_provider_from_records(records)

    formatted = "\n".join(lines)
    return f"*DNS Records:*\n{formatted}\n*Provider:* {provider}"
# get_dns_info()
