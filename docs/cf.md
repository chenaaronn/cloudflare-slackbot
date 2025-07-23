# Slash Command: Cloudflare Ray ID Lookup

This Slack integration provides a slash command (`/cf -ray [ray_id]`) that allows users to query Cloudflare Firewall Events based on a given Ray ID using the Cloudflare GraphQL Analytics API.

---

## Usage

```
/cf -ray [ray_id]
```

**Example:**

```
/cf -ray 783dd7324ebfbb62
```

If the Ray ID corresponds to a security event logged by Cloudflare within the past 30 days, the bot will return:

* IP and Country
* ASN
* Request path and query string
* Action taken (e.g., block, log, skip)
* Source of the action (e.g., WAF)
* User Agent
* Datetime

---

## Cloudflare GraphQL Query

The app uses the `firewallEventsAdaptive` dataset in the Cloudflare GraphQL Analytics API. The query is filtered to the last 30 days and the specific Ray ID:

```
action
clientAsn
clientCountryName
clientIP
clientRequestPath
clientRequestQuery
datetime
source
userAgent
```

---

## Known Limitations

* Only **security events** (blocked, challenged, logged, etc.) will return results
* **Clean** requests (e.g., HTTP 200, 301) that are not mitigated do **not** appear in `firewallEventsAdaptive`
* Cloudflare retains firewall logs for **30 days max**, so queries outside that window return nothing
* There may be a **short delay** (up to 1 minute) between when a Ray ID is generated and when it becomes available in the GraphQL dataset

---

## Cloudflare API Token Permissions

The API token used must have the following permissions:

* `Zone.Zone` → Read
* `Analytics.Read` → Read

---

## Error Responses

* `Invalid Ray ID format.` – The provided Ray ID is not a valid 16-character hex
* `No firewall events found for that Ray ID.` – The event was not mitigated, logged, or is outside the 30-day window
* `Error fetching data: [status] [message]` – Could indicate an auth issue or malformed query
