# handles /miwebsite 
import socket
import subprocess
import ipaddress
from urllib.parse import urlparse

from flask import request, Response
from ipwhois import IPWhois
import slack

from cloudflare_api import get_dns_info

def handle_miwebsite(client): 
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    text = data.get('text')

    args = text.split()
    # initial error checking
    if len(args) < 2:
        return Response("Usage: /miwebsite -cl [domain]", status=200)
    
    # acknowledge the request immediately to Slack
    # client.chat_postMessage(channel=channel_id, text="Processing your request...")

    flag = args[0] 
    # let cl be default
    # add error checking and other flags
    
    raw = args[1]
    parsed = urlparse(raw)
    domain = parsed.netloc or parsed.path  # strips http:// and trailing slashes

    if not is_valid_domain(domain):
        return Response("Invalid website domain / Domain not found", status=200)

    # default values
    host_info = "Not Found"
    ip_address = "NA"
    cloudflare = "No"
    cloudflare_content = "NA"
    cloudflare_lookup = "NA"

    # resolve domain to IP addresses
    # Resolve IPs (IPv4 + IPv6) using getaddrinfo
    try:
        infos = socket.getaddrinfo(domain, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        ip_addresses = sorted({ai[4][0] for ai in infos})
        host_info = ', '.join(ip_addresses) if ip_addresses else "Not Found"
    except Exception:
        host_info = "Not Found"
        ip_addresses = []

    # verify IP ownership
    org_names = []
    for ip in ip_addresses:
        try:
            # validate IP address
            ip_obj = ipaddress.ip_address(ip.strip())
            
            # perform RDAP lookup
            obj = IPWhois(str(ip_obj))
            res = obj.lookup_rdap()
            org = res.get('network', {}).get('name', 'Unknown')
            org_names.append(f"{ip_obj} ({org})")
        except ValueError:
            # skip invalid IP addresses
            continue
        except Exception:
            # append only valid ip addr to org_names
            org_names.append(f"{ip} (Lookup Failed)")

    # determine if any IP belongs to Cloudflare
    for org_info in org_names:
        if "cloudflare" in org_info.casefold():
            cloudflare = "Yes"
            break

    # standard output
    response_msg = (
        f"*Website:* {domain}\n"
        f"*Host:* {host_info}\n"
        f"*IP Ownership:* {', '.join(org_names)}\n"
        f"*Cloudflare:* {cloudflare}"
    )

    # note: data type with all the fields with the output **
    # class
    
    # IF CLOUDFLARE
    if cloudflare == "Yes":
        try:
            dns_records = get_dns_info(domain)
        except Exception as e:
            dns_records = f"Error: {str(e)}"
        response_msg += f"\n{dns_records}"

    client.chat_postMessage(channel=channel_id, text=response_msg)
    return Response(), 200
# handle_miwebsite()


# checks if the domain can be resolved to an IP address
def is_valid_domain(domain):
    if domain.startswith("http://") or domain.startswith("https://"):
        domain = urlparse(domain).netloc
   
    try:
        socket.gethostbyname(domain)
        return True
    except socket.gaierror:
        return False
