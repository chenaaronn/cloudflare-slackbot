# interact with the Cloudflare API, retrieve DNS records for a given domain, 
# identify its zone, and determine the IP ownership provider for those records
import requests 
import os
import socket
from ipwhois import IPWhois
import ipaddress
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file

import requests

def list_all_zones(headers):
    url = "https://api.cloudflare.com/client/v4/zones"
    params = {"page": 1, "per_page": 50}
    zones = []

    while True:
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
        data = res.json()
        zones.extend(data.get("result", []))

        info = data.get("result_info", {})
        page = info.get("page", 1)
        total = info.get("total_pages", 1)
        if page >= total:
            break
        params["page"] += 1

    return zones
# list_all_zone()

def find_zone_id_for_domain(domain, zones):
    # Collect any zones whose name matches the end of the domain
    matches = [(zone["name"], zone["id"]) for zone in zones if domain.endswith(zone["name"])]
    if not matches:
        raise Exception(f"Zone for domain '{domain}' not found.")
    # Choose the longest (most specific) matching zone name
    best_zone, best_id = max(matches, key=lambda x: len(x[0]))
    return best_id
# find_zone_id()

def list_dns_records(zone_id, headers, domain):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    params = {"page": 1, "per_page": 50}
    records = []

    while True:
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
        data = res.json()
        records.extend(
            (r["content"], r["type"])
            for r in data.get("result", [])
            if r["name"] == domain
        )

        info = data.get("result_info", {})
        page = info.get("page", 1)
        total = info.get("total_pages", 1)
        if page >= total:
            break
        params["page"] += 1

    return records
# list_dns_records()


def get_provider_from_records(records):
    providers = set()
    for content, rtype in records:
        ips_to_check = []
        if rtype in ("A", "AAAA"):
            ips_to_check.append(content)
        elif rtype == "CNAME":
            try:
                infos = socket.getaddrinfo(content, None)
                ips = {ai[4][0] for ai in infos}
                ips_to_check.extend(ips)
            except Exception:
                continue

        for ip in ips_to_check:
            try:
                ip_obj = ipaddress.ip_address(ip)
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

    """ debug
    zones = list_all_zones(headers)
    print(f"[DEBUG] Fetched {len(zones)} zones")

    # Next lines before find_zone_id_for_domain
    for z in zones[:5]:
        print("Sample zone:", z["name"])
    matches = [(z["name"], z["id"]) for z in zones if domain.endswith(z["name"])]
    print("[DEBUG] Possible zone matches:", matches)

    zone_id = find_zone_id_for_domain(domain, zones)
    """


    return f"*DNS Records:*\n{formatted}\n*Provider:* {provider}"
# get_dns_info()
