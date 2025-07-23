# Slash Command: Cloudflare Website Lookup

This Slack integration provides a slash command (`/website [domain]`) that allows users to retrieve information about a given website, including IP resolution, IP ownership, DNS records, and whether the site is using Cloudflare. If the domain is proxied by Cloudflare, it fetches associated DNS records via the Cloudflare API.

---

## Usage

```
/website [domain]
```

**Example:**

```
/website umich.edu
```

---

## Example Outputs

### `/website jeffcd10.cdn-dev.it.umich.edu`
- **Website:** jeffcd10.cdn-dev.it.umich.edu  
- **Host:** 162.159.140.37, 172.66.0.37  
- **IP Ownership:** 162.159.140.37 (CLOUDFLARENET), 172.66.0.37 (CLOUDFLARENET)  
- **Cloudflare:** Yes  
- **DNS Records:**  
  - Content: `23.185.0.3`, Type: `A`  
  - Content: `2620:12a:8001::3`, Type: `AAAA`  
  - Content: `2620:12a:8000::3`, Type: `AAAA`  
- **Provider:** PANTHEON-IP4, PANTHEON-IP6  

### `/website michigan.fulcrum.org`
- **Website:** michigan.fulcrum.org  
- **Host:** 162.159.140.37, 172.66.0.37  
- **IP Ownership:** 162.159.140.37 (CLOUDFLARENET), 172.66.0.37 (CLOUDFLARENET)  
- **Cloudflare:** Yes  
- **DNS Records:**  
  - Content: `fulcrum-lb.umdl.umich.edu`, Type: `CNAME`  
- **Provider:** UMICH-4866  

---

## DNS Records Table

### 1. Type
Specifies the DNS record type, which determines the purpose of the record. Common types include:

- **A**: Maps a domain to an **IPv4** address  
- **AAAA**: Maps a domain to an **IPv6** address  
- **CNAME**: Maps a domain to **another domain name**  
- **MX**: Directs email to a **mail server**  
- **TXT**: Holds **arbitrary text data**, often for verification purposes  

### 2. Name
Indicates the **hostname** or **subdomain** for the record.

### 3. Content
Contains the **value** associated with the record type:

- For **A/AAAA** records: the **IP address**  
- For **CNAME** records: the **target domain name**  
- For **MX** records: the **mail server domain**  
- For **TXT** records: the **text string**  

---

## Functionality Overview

* Resolves host IP addresses for the domain
* Performs RDAP lookups to identify IP ownership
* Checks for Cloudflare proxying by analyzing org names
* If proxied by Cloudflare, retrieves:

  * DNS record types and contents
  * Hosting provider info via WHOIS on DNS record IPs

---

## Cloudflare API Endpoints Used

* `GET /zones` — to list all available zones
* `GET /zones/:zone_id/dns_records` — to retrieve DNS records for a domain

---

## Known Limitations

* Some domains may not resolve if DNS is misconfigured or unavailable
* If the site is not proxied by Cloudflare, DNS record and provider information will not be queried via Cloudflare
* RDAP and DNS record queries may occasionally time out depending on network reliability

---

## Cloudflare API Token Permissions

The API token used must have the following permissions:

* `Zone.Zone` → Read
* `Zone.DNS` → Read

---

## Error Responses

* `Invalid website domain / Domain not found.` – Domain name was invalid or could not be resolved
* `No DNS records found.` – No matching DNS records for the domain
* `Error: [message]` – Issue occurred during DNS or WHOIS lookup

---

## Dependencies

* Python 3.x
* Flask
* slack\_sdk
* ipwhois
* requests

---