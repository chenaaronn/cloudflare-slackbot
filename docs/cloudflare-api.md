# Cloudflare API Endpoints (calls) Used 

## 1. List Zones

- **Endpoint:** `GET /zones`
- **Description:** Retrieves all zones (domains) associated with the Cloudflare account.  
- **Purpose:** Used to find all domains under the account to identify the correct zone ID for a given domain.

## 2. List DNS Records

- **Endpoint:** `GET /zones/:zone_identifier/dns_records`
- **Description:** Retrieves DNS records (such as A, AAAA, CNAME, MX, TXT) for a specific zone identified by `zone_identifier`.  
- **Purpose:** Used to fetch all DNS records for the given domain’s zone to analyze IP addresses and related information.

