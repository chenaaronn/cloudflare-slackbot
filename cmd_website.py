import socket
import ipaddress
from urllib.parse import urlparse
from ipwhois import IPWhois

from cloudflare_utils import get_dns_info

def handle_website(client, channel_id, text):
    args = text.split()
    if len(args) < 1:
        client.chat_postMessage(channel=channel_id, text="Usage: /website [website URL]")
        return {"statusCode": 200, "body": ""}

    domain = args[0]
    client.chat_postMessage(channel=channel_id, text=f"Gathering info about `{domain}`...")

    return process_website(client, domain, channel_id)
# handle_website()

def process_website(client, domain, channel_id):
    parsed = urlparse(domain)
    domain = parsed.netloc or parsed.path

    if not is_valid_domain(domain):
        client.chat_postMessage(channel=channel_id, text="Invalid website domain / Domain not found.")
        return {"statusCode": 200, "body": ""}

    try:
        infos = socket.getaddrinfo(domain, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        ip_addresses = sorted({ai[4][0] for ai in infos})
        host_info = ', '.join(ip_addresses) if ip_addresses else "Not Found"
    except Exception:
        host_info = "Not Found"
        ip_addresses = []

    org_names = []
    for ip in ip_addresses:
        try:
            ip_obj = ipaddress.ip_address(ip.strip())
            obj = IPWhois(str(ip_obj))
            res = obj.lookup_rdap()
            org = res.get('network', {}).get('name', 'Unknown')
            org_names.append(f"{ip_obj} ({org})")
        except Exception:
            org_names.append(f"{ip} (Lookup Failed)")

    cloudflare = "Yes" if any("cloudflare" in org.casefold() for org in org_names) else "No"

    response_msg = (
        f"*Website:* {domain}\n"
        f"*Host:* {host_info}\n"
        f"*IP Ownership:* {', '.join(org_names)}\n"
        f"*Cloudflare:* {cloudflare}"
    )

    if cloudflare == "Yes":
        try:
            dns_records = get_dns_info(domain)
            response_msg += f"\n{dns_records}"
        except Exception as e:
            response_msg += f"\nDNS Lookup Error: {str(e)}"

    try:
        client.chat_postMessage(channel=channel_id, text=response_msg)
    except Exception as e:
        print(f"❌ Failed to post message: {e}")

    return {"statusCode": 200, "body": ""}
# process_website()

# checks if the domain can be resolved to an IP address
def is_valid_domain(domain):
    if domain.startswith("http://") or domain.startswith("https://"):
        domain = urlparse(domain).netloc

    try:
        socket.gethostbyname(domain)
        return True
    except socket.gaierror:
        return False
